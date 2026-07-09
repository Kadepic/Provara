#!/usr/bin/env python3
"""
COUCHE CONVERSATIONNELLE de l'interface — rendre l'assistant capable de RÉPONDRE, sans jamais inventer.

Deux étages, du plus léger au plus lourd. On ne franchit l'étage suivant que si le précédent n'a rien de SOUND.

  ÉTAGE 1 — MÉMOIRE DE DIALOGUE (léger, toujours actif). C'est le cœur anti-éphémère du projet : l'assistant
  répond avec ce que l'utilisateur lui a RÉELLEMENT dit (verbatim), retrouvé par `conversation.rappelle`
  (index inversé idf, non borné par le contexte). Dis-lui ton nom dans une conversation, il s'en souvient dans
  une autre. SOUNDNESS : on n'utilise comme réponse qu'un ÉNONCÉ de l'utilisateur (role 'user', NON interrogatif)
  — une question ne répond pas à une question — et jamais le message courant lui-même.

  ÉTAGE 2 — CONNAISSANCE BORNÉE VÉRIFIÉE (lourd, OPT-IN via IA_PLEINE=1). Interroge le lecteur du borné
  (`ia.donnee_nl`) : renvoie un fait VÉRIFIÉ ou RIEN (jamais d'invention). Import PARESSEUX (via importlib pour
  ne pas créer de dépendance statique) : par défaut l'interface NE charge PAS le lecteur (≈622 Mo) → légère,
  OOM-safe en cohabitation avec T1/T2. On ne paie le chargement que si l'utilisateur l'a explicitement activé.

  ÉTAGE 0 — HONNÊTETÉ : si aucun étage n'a de réponse réelle, on le DIT (« je n'ai rien en mémoire »). Jamais
  de réponse fabriquée. C'est la même règle FAUX=0 que tout le projet.
"""
from __future__ import annotations

import importlib
import json
import os
import re

_ICI = os.path.dirname(os.path.abspath(__file__))
_HARNAIS = os.path.dirname(_ICI)
# Priorité à l'env posé par verax_boot/lance : dans le .exe (PyInstaller), __file__ ne pointe PAS sous _MEIPASS
# pour les modules gelés -> le chemin dérivé serait faux et les requêtes inverses seraient mortes en silence.
_DOSSIER_LECTEUR = os.environ.get("LECTEUR_DATASETS_DIR") or os.path.join(_HARNAIS, "datasets", "lecteur")

# Indices de DEMANDE — pour ne pas dépendre du « ? » (l'utilisateur l'oublie souvent). Si l'un de ces mots
# apparaît N'IMPORTE OÙ (forme sans accent), on considère que l'utilisateur attend une réponse. Liste choisie
# pour être discriminante (on évite « ou »/« que », trop courants en affirmation). Sert UNIQUEMENT à choisir le
# message quand rien n'est trouvé (« noté » vs « je n'ai pas l'info ») et à autoriser le rappel de dialogue ;
# la CONNAISSANCE vérifiée, elle, est tentée de toute façon (donc une question sans « ? » obtient sa réponse).
_INDICES_DEMANDE = frozenset(
    "comment pourquoi quand combien quel quelle quels quelles quoi qui lequel laquelle lesquels lesquelles "
    "sais connais peux saurais pourrais souviens rappelle rappelles dis explique donne montre cherche trouve "
    " recherche "
    # impératifs de CALCUL/CONVERSION/TRADUCTION : une demande, jamais un fait à mémoriser (sinon « Convertis 5 km
    # en mètres » était classé affirmation -> « C'est noté ». Sound : ne change que le message/gating, jamais un fait).
    "convertis convertir calcule calculer compte resous resoudre resolve traduis traduire encode encoder "
    "decode decoder transcris transcrire".split()
)

# Import paresseux de normalise (sans accents/ponctuation) — base_faits est léger, déjà dans la clôture.
try:
    from base_faits import normalise as _normalise
except Exception:                                   # robustesse : repli minimal si indisponible
    def _normalise(s):
        return str(s).lower()


def _veut_reponse(texte: str) -> bool:
    """L'utilisateur attend-il une réponse (question) plutôt qu'il n'affirme un fait ? Tolérant au « ? » oublié
    et aux fautes de ponctuation : « ? » présent N'IMPORTE OÙ, OU un mot-indice de demande présent, OU un
    NOMINAL-REQUÊTE nu (« distance entre Paris et Madrid », « définition de sérendipité » : une tête d'attribut
    suivie de son connecteur EST une demande, même sans point d'interrogation)."""
    if "?" in texte:
        return True
    tn = _normalise(texte)
    # DEMANDE D'INTERACTION à la 2e personne (« je voudrais que tu me challenges sur… », « peux-tu me
    # parler de… ») : c'est une REQUÊTE, jamais un fait à noter (Yohan 2026-07-06 : parti en mémo !).
    if re.search(r"\b(?:peux[- ]tu|pourrais[- ]tu|je\s+voudrais\s+que\s+tu|j\s*aimerais\s+que\s+tu|"
                 r"tu\s+peux|challenge|defie|teste[- ]moi|interroge[- ]moi)\b", tn):
        return True
    toks = tn.split()
    if set(toks) & _INDICES_DEMANDE:
        return True
    if len(toks) >= 3 and toks[1] in ("de", "du", "des", "d", "entre") and not (set(toks) & _TOKENS_AFFIRMATION):
        try:
            return toks[0] in _attr_heads() or toks[0] in ("distance", "definition", "difference")
        except Exception:
            return False
    return False


# Marqueurs d'AFFIRMATION : verbe conjugué courant (copule, avoir, verbes d'état personnels) ou 1ʳᵉ personne.
# « à » normalisé donne « a » -> on N'INCLUT PAS « a » (sinon « recette à la pomme » serait une affirmation).
_TOKENS_AFFIRMATION = frozenset(
    "est sont etait etaient sera seront suis sommes etes ai avons avez ont avait avaient aura auront "
    "appelle appellent habite habitent travaille travaillent aime aiment adore prefere deteste "
    "je j mon ma mes notre nos".split())
# Interjections/acquiescements : PAS des sujets de recherche (« oui » orphelin -> accusé, pas une quête web).
_INTERJECTIONS = frozenset(
    "oui non ok okay dac daccord merci super genial parfait cool bien compris entendu voila ah oh hum hmm "
    "euh bof stp svp please bravo chouette top nickel impec".split())


# Verbes d'ACTION à l'impératif (carte FERMÉE) : un ordre commençant par l'un d'eux, si AUCUN cap ne l'a
# exécuté, mérite le repli honnête, pas un « C'est noté ». EXCLUS volontairement : les verbes de MÉMORISATION
# (note, retiens, rappelle, souviens) — « rappelle-moi d'acheter du pain » reste un mémo légitime.
_VERBES_IMPERATIFS = frozenset(
    "equilibre range resous resume corrige complete trie classe melange transforme genere fabrique "
    "construis assemble ordonne factorise developpe simplifie additionne multiplie divise soustrais arrondis "
    "convertis calcule compte compare explique decris definis liste cite nomme trouve cherche montre "
    "dessine trace affiche traduis code decode chiffre dechiffre encode inverse permute combine".split())


def _est_demande_imperative(texte: str) -> bool:
    """La phrase est-elle un ORDRE (verbe d'action en tête de la carte fermée) ? Utilisé UNIQUEMENT au terminal
    (aucun cap n'a répondu) pour préférer le repli honnête au mémo. Le premier mot de contenu doit être un verbe
    d'action ; « peux-tu / stp » en préambule sont dépouillés d'abord."""
    n = _normalise(texte)
    n = re.sub(r"^(?:s il te plait|stp|svp|peux[- ]tu|pourrais[- ]tu|tu peux|allez|aller)\s+", "", n).strip()
    tete = n.split()[0] if n.split() else ""
    return tete in _VERBES_IMPERATIFS


def _semble_affirmation(texte: str) -> bool:
    """Y a-t-il quelque chose à NOTER ? Une affirmation porte un verbe conjugué courant, une marque de première
    personne, ou une VALEUR (chiffre : « rdv dentiste mardi 15h » reste un mémo). Une PHRASE NOMINALE nue
    (« histoire du château de Chambord », « symptômes de la carence en fer ») n'affirme RIEN : c'est un SUJET
    DE RECHERCHE — répondre « C'est noté » était répondre à côté (principe : chercher/clarifier, jamais classer
    arbitrairement). Sound : ne change que le ROUTAGE du message, jamais un fait."""
    if any(c.isdigit() for c in texte):
        return True
    toks = _normalise(texte).split()
    if set(toks) & _TOKENS_AFFIRMATION:
        return True
    # aucun mot de CONTENU (que des interjections/mots-outils courts) -> rien à chercher : accusé de réception
    return not any(len(m) >= 3 and m not in _INTERJECTIONS for m in toks)


# Une question de MESURE (poids/masse/taille/diamètre/température…) attend une réponse NUMÉRIQUE. Si le lookup a
# répondu une valeur SANS chiffre, c'est qu'il a résolu un SOUS-lookup catégoriel (« combien pèse la capitale de la
# France » -> « Paris ») en IGNORANT l'attribut de mesure non satisfiable -> réponse à la MAUVAISE question. Garde
# PUREMENT PROTECTRICE et SOUND : toute VRAIE réponse de mesure contient un nombre, donc elle ne supprime jamais une
# bonne réponse (elle ne fait que rejeter un mismatch). (accents retirés par _normalise : pèse->pese, diamètre->diametre.)
_MESURE_RE = re.compile(
    r"combien (?:pese|pesent|mesure|mesurent)\b"
    r"|\b(?:poids|masse|taille|diametre|hauteur|longueur|largeur|temperature|superficie|altitude|"
    r"epaisseur|profondeur|densite|volume|circonference|envergure)\s+(?:de |du |des |d['e])")


def _est_question_mesure(texte: str) -> bool:
    return bool(_MESURE_RE.search(_normalise(texte)))


def _reponse_incoherente_mesure(question: str, reponse: str) -> bool:
    """True si `question` demande une MESURE mais `reponse` ne contient AUCUN chiffre (mismatch : sous-lookup
    catégoriel résolu à la place de l'attribut de mesure). Sound : ne rejette qu'une réponse non numérique.
    MÊME FILET pour les questions de DATE (« quand a eu lieu X ») : une réponse sans année (« Battle » — la
    VILLE du lieu de la bataille d'Hastings, servie par un sous-lookup) est un mismatch de type -> rejetée."""
    if _est_question_mesure(question) and not any(c.isdigit() for c in reponse):
        return True
    qn = _normalise(question)
    if re.search(r"^\s*quand\b|\ba quelle date\b|\ben quelle annee\b|\bquelle annee\b", qn):
        return not re.search(r"\b\d{3,4}\b", reponse)     # une vraie réponse de date contient une année
    return False


# GARDE RELATIONS IMBRIQUÉES « X de [la] Y de Z » : le moteur résout la relation INTERNE (« Y de Z ») et renvoie son
# entité en IGNORANT l'attribut EXTERNE X → réponse du MAUVAIS TYPE (« monnaie de la capitale de la France » → Paris ;
# « langue de la capitale de l'Allemagne » → Berlin ; « synonyme de la capitale de la France » → Paris). On ne sait
# pas COMPOSER deux relations → on abstient (HORS honnête). SOUND/surgical : on n'abstient QUE si l'attribut INTERNE Y
# est un VRAI token-attribut de relation, précédé d'un mot de CONTENU via « de », ET suivi de son propre « de <entité> »
# — sinon « capitale de la République de Chine » (entité multi-mot) ou « capitale de la France » (simple) ne matchent pas.
_NEST_SCAFFOLD = frozenset(
    "quel quelle quels quelles est ce c qu quoi la le les un une de du des au aux en et dis donne sais connais "
    "peux pourrais saurais montre cherche trouve explique rappelle souviens comment alors voila donc stp svp "
    "bien je tu il elle on me te savoir voudrais aimerais nous vous mais".split())
_NEST_RE = re.compile(r"\b(\w+)\s+(?:de la|de l|de|du|des)\s+(?:la |le |les |un |une )?(\w+)\b")
_ATTR_HEADS_CACHE = None


def _attr_heads() -> set:
    """Tokens-ATTRIBUT (tête de relation) connus = têtes des relations du lecteur + un noyau de base. Sert à
    détecter une relation IMBRIQUÉE (l'inner « Y de Z » est une vraie relation, pas une entité multi-mot)."""
    global _ATTR_HEADS_CACHE
    if _ATTR_HEADS_CACHE is None:
        heads = {r.split("_")[0] for r in _relations()}
        heads = {h for h in heads if len(h) >= 4 and h not in _GENERIQUES}
        # NOYAU de relations ajouté APRÈS le filtre : « pays », « continent »… sont des RELATIONS légitimes même
        # si présentes dans _GENERIQUES — sans ça, « continent du pays de Paris » n'était pas vu comme imbriqué.
        heads |= {"capitale", "monnaie", "langue", "numero", "masse", "population", "continent", "drapeau",
                  "hymne", "gentile", "superficie", "altitude", "diametre", "temperature", "pays", "region",
                  "auteur", "compositeur", "realisateur", "createur", "inventeur", "fondateur"}
        _ATTR_HEADS_CACHE = heads
    return _ATTR_HEADS_CACHE


def _est_relation_imbriquee(texte: str) -> bool:
    """True si la question imbrique deux relations « X de [la] Y de Z » (Y = vrai attribut, X = mot de contenu)."""
    qn = _normalise(texte)
    heads = _attr_heads()
    for m in _NEST_RE.finditer(qn):
        outer, inner = m.group(1), m.group(2)
        # inner == outer AUTORISÉ : une relation RÉPÉTÉE (« diamètre du diamètre de Jupiter », « auteur de l'auteur des
        # Misérables », « genre du genre du mot table ») est dégénérée -> HORS (le lookup interne fuyait sinon).
        if (inner in heads and outer not in _NEST_SCAFFOLD and not outer.isdigit()
                and re.search(rf"\b{re.escape(inner)}\s+(?:de|du|des|de la|de l)\b", qn)):
            return True
    return False


# « X de [la] Y de [la] Z » : outer=X, inner=Y (relation), Z=entité (possiblement multi-mot).
_NEST_PARSE = re.compile(
    r"^\s*(?:(?:quel(?:le)?s?|quoi|qu['e ]?est[- ]?ce que|c['e ]?est|donne(?:s|z)?[- ]?moi|dis[- ]?moi|"
    r"peux[- ]?tu(?:\s+me)?|sais[- ]?tu|connais[- ]?tu)\s+)*"
    r"(?:est\s+|la\s+|le\s+|les\s+|l['] ?)*"
    r"([\wà-ÿ]+)\s+(?:de\s+la|de\s+l['] ?|du|des|de)\s+(?:la\s+|le\s+|les\s+|l['] ?)?"
    r"([\wà-ÿ]+)\s+(?:de\s+la|de\s+l['] ?|du|des|de)\s+(?:la\s+|le\s+|les\s+|l['] ?)?(.+?)\s*\??\s*$", re.I)


def _val_par_famille(ia, rel_head: str, entite: str):
    """Résout « rel_head de entité » via la FAMILLE de relations à tête `rel_head` (« pays » -> pays_de_capitale,
    pays_de_ville…) : lookup EXACT de l'entité dans chaque relation de la famille. FAUX=0 : ne renvoie une valeur
    QUE si elle est UNIQUE across la famille (si deux relations donnent des valeurs différentes = ambigu -> None).
    Permet à « pays de Paris » de trouver la relation `pays_de_capitale` sans correction floue."""
    try:
        lec = getattr(ia, "_LEC", None)
        lec = getattr(lec, "LECTEUR", None) if lec else None
        if lec is None:
            return None
        h = _normalise(rel_head)
        rels = [r for r in lec.relations() if r == h or r.split("_")[0] == h or r.startswith(h + "_")]
        vals = set()
        for r in rels:
            f = lec.cherche(r, entite)
            if f is not None:
                v = getattr(f, "valeur", None)
                if v is not None:
                    vals.add(v)
        return next(iter(vals)) if len(vals) == 1 else None
    except Exception:
        return None


def _val_verifiee(ia, verifie, requete: str, rel_head: str = None, entite: str = None):
    """Valeur VÉRIFIÉE d'une requête « relation de entité » par lookup EXACT (PAS de correction floue : dans une
    CHAÎNE, une correction floue d'un maillon propagerait une erreur — FAUX=0 exige l'exactitude). Essaie le
    lookup NL exact, puis la FAMILLE de relations (rel_head/entité) si fournie. None si non résolu."""
    try:
        statut, fait = ia.donnee_nl(requete)
        if fait is not None and statut == verifie:
            return getattr(fait, "valeur", None)
    except Exception:
        pass
    if rel_head and entite:
        v = _val_par_famille(ia, rel_head, entite)
        if v is not None:
            return v
        return _lookup_direct(rel_head, entite)       # repli INSENSIBLE AUX ACCENTS (« Nigéria »≡« Nigeria »)
    return None


# Tokens de relations d'ŒUVRES D'ART : une entité MONUMENT (présente dans ville_monument) ne doit JAMAIS être
# servie par ces relations — « hauteur de la tour Eiffel » matchait « La Tour Eiffel » (un TABLEAU, 0,632 m !).
# Le tableau homonyme reste servi pour une vraie œuvre (« hauteur de la Joconde » : la Joconde n'est pas un
# monument). Liste FERMÉE des supports d'art des datasets.
_RELS_OEUVRE_ART = frozenset(("peinture", "estampe", "aquarelle", "dessin", "gravure", "photographie",
                              "lithographie", "tableau", "affiche", "icone"))


def _est_monument(entite: str) -> bool:
    try:
        return bool(_lookup_cell("ville_monument", entite))
    except Exception:
        return False


def _est_tableau_connu(entite: str) -> bool:
    """L'entité est-elle une PEINTURE connue (clé de peintre_oeuvre, avec ou sans article) ? Sert au type-check
    homonyme : la hauteur d'une SCULPTURE « La Joconde » (2,48 m) n'est pas celle du tableau de Vinci."""
    try:
        for var in (entite, "la %s" % entite, "le %s" % entite):
            if _lookup_cell("peintre_oeuvre", var):
                return True
    except Exception:
        pass
    return False


def _lookup_direct(rel_head: str, entite: str):
    """Lookup « rel_head de entite » INSENSIBLE AUX ACCENTS/CASSE, lu directement des .jsonl (contourne les
    incohérences de nommage entre relations : « Nigéria » vs « Nigeria »). FAUX=0 : normalisation d'accent =
    IDENTITÉ préservée (pas du flou Levenshtein) ; valeur renvoyée seulement si UNIQUE across la famille ;
    GARDE MONUMENT≠ŒUVRE : un monument connu n'est pas servi par une relation d'œuvre d'art homonyme."""
    h = _normalise(rel_head)
    vals = set()
    est_monu = None                              # calculé PARESSEUSEMENT (1 lookup) et seulement si besoin
    rels_h = _RELS_PAR_TETE.get(h)               # matching tête->relations MÉMOÏSÉ (le split par relation se
    if rels_h is None:                           # refaisait à chaque appel — même famille d'atome que _rel_toks)
        rels_h = [r_ for r_ in _relations()
                  if r_ == h or r_.split("_")[0] == h or r_.startswith(h + "_")]
        _RELS_PAR_TETE[h] = rels_h
    try:
        for rel in rels_h:
            if any(tk in _RELS_OEUVRE_ART for tk in rel.split("_")[1:]):
                if est_monu is None:
                    est_monu = _est_monument(entite)
                if est_monu:                     # l'œuvre homonyme du MONUMENT est un piège -> ignorée
                    continue
            # RAM-sûr : _lookup_cell fait un scan STREAMING sur les gros fichiers (occupation_personne 135 Mo,
            # nationalite_personne 143 Mo, taxon_parent 216 Mo…) au lieu de matérialiser tout le dict.
            cell = _lookup_cell(rel, entite)
            if cell and cell[1] is not None:
                vals.add(cell[1])
    except Exception:
        return None
    return next(iter(vals)) if len(vals) == 1 else None


def _lookup_famille(rel_head: str, entite: str) -> list:
    """Toutes les valeurs « rel_head de entite » across la famille : [(relation, affiché, valeur)]. Même garde
    monument≠œuvre que _lookup_direct ; les TITRES stockés AVEC article sont aussi essayés (« Joconde » ->
    « La Joconde »). Sert à DIRE l'ambiguïté au lieu de laisser la cascade en piocher une."""
    h = _normalise(rel_head)
    out = []
    est_monu = None
    variantes = [entite] + ["%s %s" % (art, entite) for art in ("la", "le")
                            if not _normalise(entite).startswith(("la ", "le ", "l "))]
    est_tableau = None
    try:
        for rel in _relations():
            if rel == h or rel.split("_")[0] == h or rel.startswith(h + "_"):
                toks = rel.split("_")[1:]
                if any(tk in _RELS_OEUVRE_ART for tk in toks) or "sculpture" in toks or "statue" in toks:
                    if est_monu is None:
                        est_monu = _est_monument(entite)
                    if est_monu:
                        continue
                if "sculpture" in toks or "statue" in toks:
                    # type-check homonyme : une PEINTURE connue n'est pas servie par une SCULPTURE homonyme
                    # (« hauteur de la Joconde » -> sculpture « La Joconde » 2,48 m, pas le tableau de Vinci)
                    if est_tableau is None:
                        est_tableau = _est_tableau_connu(entite)
                    if est_tableau:
                        continue
                for var in variantes:
                    cell = _lookup_cell(rel, var)
                    if cell and cell[1] is not None:
                        out.append((rel, cell[0], cell[1], var is variantes[0]))   # exact (sans article) ?
                        break
    except Exception:
        pass
    # le match EXACT prime : « superficie de la France » = le PAYS (relation superficie), pas le hameau
    # « La France » (superficie_localite, via la variante d'article). Les variantes ne servent que s'il
    # n'existe AUCUN match exact (titres d'œuvres stockés avec article : « La Joconde »).
    exacts = [c for c in out if c[3]]
    return [(r, a, v) for r, a, v, _x in (exacts or out)]


def _compose_relations(texte: str):
    """RAISONNEMENT COMPOSITIONNEL « X de Y de Z » : résout l'INNER (Y de Z) -> entité E vérifiée, puis l'OUTER
    (X de E) -> valeur vérifiée. FAUX=0 : chaque maillon est un lookup VÉRIFIÉ ; si un maillon manque -> None
    (abstention honnête, jamais une composition inventée). Renvoie la réponse + la chaîne de dérivation."""
    m = _NEST_PARSE.match(texte)
    if not m:
        return None
    outer, inner, z = m.group(1).strip(), m.group(2).strip(), m.group(3).strip(" ?.\"'«»")
    heads = _attr_heads()
    nn = _normalise
    if nn(inner) not in heads or nn(outer) in _NEST_SCAFFOLD or nn(outer) not in heads:
        return None                                   # inner ET outer doivent être de vraies relations
    ia, verifie = _charge_ia()
    if not ia:
        return None
    e = _val_verifiee(ia, verifie, "%s de %s" % (inner, z), rel_head=inner, entite=z)     # maillon 1 : Y de Z = E
    if not e:
        return None
    v = _val_verifiee(ia, verifie, "%s de %s" % (outer, e), rel_head=outer, entite=e)     # maillon 2 : X de E
    if not v:
        return None
    return "%s  (en composant : %s de %s = %s, puis %s de %s)" % (v, inner, z, e, outer, e)


# ————————————————————— RAISONNEMENT COMPOSITIONNEL N-SAUTS (pensée machine : chaîne EXACTE + dérivation) —————————————
# Généralise `_compose_relations` (2 sauts, regex) à une PROFONDEUR ARBITRAIRE : « la monnaie de la capitale du pays
# de <X> », etc. Descente récursive : on épluche la relation de TÊTE, on résout récursivement le RESTE en une entité
# VÉRIFIÉE, puis on applique la tête. FAUX=0 : chaque maillon est un lookup vérifié ; un maillon manquant -> abstention
# (jamais une composition inventée). La force machine : la dérivation complète est MONTRÉE et re-vérifiable.
# Profondeur : PAS de limite conceptuelle (pensée machine). La récursion opère sur le « reste » après un connecteur,
# qui RACCOURCIT strictement à chaque saut -> terminaison naturelle garantie. Ce plafond n'est qu'un garde-fou très
# large contre une entrée pathologique ; aucune vraie question ne l'approche.
_MAX_SAUTS = 64
_CONNECTEUR_RE = re.compile(r"\s+(?:de\s+la|de\s+l['’]|du|des|de|d['’])\s+", re.I)
# habillage interrogatif à retirer avant de parser l'expression nominale composée.
_HABILLAGE_RE = re.compile(
    r"^\s*(?:quel(?:le)?s?\s+(?:est|sont)\s+|qu['e ]?\s*est[- ]?ce\s+que\s+|c['e ]?\s*est\s+quoi\s+|"
    r"c['e ]?\s*est\s+|donne(?:s|z)?[- ]?moi\s+|dis[- ]?moi\s+|peux[- ]?tu(?:\s+me)?\s+dire\s+|"
    r"sais[- ]?tu\s+|connais[- ]?tu\s+)+", re.I)

# LANGAGE SMS léger : carte FERMÉE token -> forme pleine (« c ki ki a écrit… » -> « c'est qui qui a écrit… »).
# Prudence FAUX=0 : uniquement des abréviations SANS lecture alternative en français standard (« ou » reste
# intact : c'est un vrai mot). Appliqué token par token, jamais dans un mot.
_SMS_MAP = {"ki": "qui", "koi": "quoi", "kel": "quel", "kelle": "quelle", "keske": "qu'est-ce que",
            "pk": "pourquoi", "pq": "pourquoi", "qd": "quand", "cmb": "combien", "cb": "combien",
            "cmt": "comment",
            "c": "c'est", "cest": "c'est", "bcp": "beaucoup", "bjr": "bonjour", "slt": "salut"}
_SMS_RE = re.compile(r"\b(" + "|".join(sorted(_SMS_MAP, key=len, reverse=True)) + r")\b(?!['’])", re.I)


def _desms(texte: str) -> str:
    """Déplie les abréviations SMS fermées vers le français plein. Identité si rien à déplier. Le lookahead
    (?!['’]) protège les élisions : le « c » de « c'est » n'est PAS une abréviation."""
    return _SMS_RE.sub(lambda m: _SMS_MAP[m.group(1).lower()], texte)


# ALIAS DE PERSONNES CÉLÈBRES (carte FERMÉE, identités incontestables — le MÊME être humain) : l'usager dit
# « Napoléon Bonaparte », toutes les relations de personnes des datasets sont clées « Napoléon Ier ». Chaque
# entrée est vérifiée contre les clés réelles avant d'être ajoutée ici. Insensible accents/casse.
_ALIAS_PERSONNE = {
    "napoleon bonaparte": "Napoléon Ier",
    "bonaparte premier": "Napoléon Ier",
    "napoleon 1er": "Napoléon Ier",
    "napoleon": "Napoléon Ier",     # nu = l'Empereur (garde ordinale dans le motif : « Napoléon III » intact)
    # MONONYMES CÉLÈBRES : le nom NU matche un HOMONYME obscur des datasets (« Mozart » -> footballeur
    # brésilien né en 1979 !, « Bach » -> né en 1882). La lecture dominante est incontestable ; cible = clé
    # réelle vérifiée (ou nom complet absent -> abstention honnête, toujours mieux qu'un homonyme faux).
    "mozart": "Wolfgang Amadeus Mozart",
    "beethoven": "Ludwig van Beethoven",
    # ⚠ la clé « Johann Sebastian Bach » des datasets est le PETIT-FILS homonyme exact (peintre, Berlin 1748) —
    # le compositeur (Eisenach 1685) est ABSENT de l'extraction. On route vers la forme française (absente) :
    # abstention honnête, toujours mieux que le petit-fils ou l'acteur de 1882 que matchait le nom nu.
    "bach": "Jean-Sébastien Bach",
    "einstein": "Albert Einstein",
    "picasso": "Pablo Picasso",
    "shakespeare": "William Shakespeare",
    "churchill": "Winston Churchill",
    "darwin": "Charles Darwin",
    "newton": "Isaac Newton",
    "gandhi": "Mohandas Karamchand Gandhi",     # clé réelle des datasets (« Mahatma » est un titre)
    "mahatma gandhi": "Mohandas Karamchand Gandhi",
}
_ACCENTS_CLS = {"a": "aàâä", "e": "eèéêë", "i": "iîï", "o": "oôö", "u": "uùûü", "c": "cç"}


def _motif_accent_tolerant(cle: str) -> str:
    """« napoleon 1er » -> motif regex qui matche aussi « Napoléon 1er » (classes accentuées, espaces souples)."""
    return "".join(("[%s]" % _ACCENTS_CLS[c]) if c in _ACCENTS_CLS else (r"\s+" if c == " " else re.escape(c))
                   for c in cle)


_ALIAS_PERSONNE_RE = re.compile(
    r"\b(" + "|".join(sorted((_motif_accent_tolerant(k) for k in _ALIAS_PERSONNE), key=len, reverse=True)) + r")\b"
    r"(?!\s*(?:I(?:er|II|I|V)?|1er|2|3|premier|deuxi[eè]me|troisi[eè]me)\b)",   # « Napoléon III » reste intact
    re.I)


def _applique_alias_personne(texte: str) -> str:
    """Remplace un alias de personne par la clé réelle des datasets (accent-insensible). Identité sinon.
    GARDE : si le nom COMPLET cible est déjà dans le texte (« Wolfgang Amadeus Mozart »), le mononyme qu'il
    contient (« mozart ») n'est PAS re-remplacé (sinon imbrication monstrueuse)."""
    tn = _normalise(texte)

    def _rempl(m):
        cle = re.sub(r"\s+", " ", _normalise(m.group(1)))
        cible = _ALIAS_PERSONNE.get(cle)
        if not cible or _normalise(cible) in tn:
            return m.group(1)
        return cible
    return _ALIAS_PERSONNE_RE.sub(_rempl, texte)


import threading as _threading

_REJEU = _threading.local()


def _rejoue(memoire, conv_id, texte: str, pleine: bool):
    """REJEU borné d'une réécriture (SMS/dévoilement/recadrage/pronom/continuation) : chaque tour de réécriture
    repasse par le pipeline complet, avec un PLAFOND de profondeur — un enchaînement de règles qui bouclerait
    (réécriture non idempotente) s'arrête net au lieu d'un RecursionError. Thread-safe (serveur multi-thread)."""
    prof = getattr(_REJEU, "prof", 0)
    if prof >= 6:
        return None
    _REJEU.prof = prof + 1
    try:
        return _repond_noyau(memoire, conv_id, texte, pleine=pleine)
    finally:
        _REJEU.prof = prof


# ENROBAGE CONVERSATIONNEL (fossé de généralisation) : les caps s'ancrent en ^ — « dis-moi qui a écrit 1984 »
# ratait alors que « qui a écrit 1984 » répond. Couche FERMÉE de préfixes de politesse/remplissage à DÉVOILER
# (la question nue est REJOUÉE d'abord ; si elle ne donne rien de mieux, l'original reprend — zéro perte).
_DEVOILE_RE = re.compile(
    r"^\s*(?:et\s+(?=(?:dis|dites|donne|rappelle|rappelez|peux|pouvez|sais|savez|tu\s|vous\s|j['’]|je\s))|"
    r"(?:dis|dites)[- ]?(?:moi|nous)\s+|donne(?:s|z)?[- ]?(?:moi|nous)\s+|"
    r"j['’ ]\s*aimerais(?:\s+(?:bien|beaucoup|tellement|tant))?\s+savoir\s+|"
    r"je\s+(?:veux|voudrais|souhaite(?:rais)?)\s+savoir\s+|"
    r"(?:est[- ]?ce\s+que\s+)?(?:tu\s+peux|peux[- ]?tu|pouvez[- ]?vous|vous\s+pouvez)\s+(?:me|nous)\s+dire\s+|"
    r"sais[- ]?tu\s+|savez[- ]?vous\s+|(?:est[- ]?ce\s+que\s+)?tu\s+sais\s+|"
    r"j['’] ?ai\s+oublié\s+|je\s+ne\s+sais\s+plus\s+|je\s+me\s+demande(?:\s+bien)?\s+|"
    # « rappelle-moi » n'est une politesse QUE devant une question (« rappelle-moi qui a écrit… ») — devant
    # de+INFINITIF ou « que » c'est un RAPPEL-TÂCHE à stocker (« rappelle-moi d'acheter du pain »), protégé
    # du dévoilement (sinon _cap_rappel ne voyait jamais la forme complète, vécu 2026-07-08).
    r"tu\s+te\s+souviens\s+(?:de\s+)?|vous\s+vous\s+souvenez\s+(?:de\s+)?|"
    r"rappelle[- ]?moi\s+(?!(?:demain|ce\s+soir|lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)?\s*"
    r"(?:de\s+|d['’]\s*)[a-zà-ÿ]+(?:er|ir|re|oir)\b|que\s+)|"
    r"rappelez[- ]?moi\s+(?!(?:de\s+|d['’]\s*)[a-zà-ÿ]+(?:er|ir|re|oir)\b|que\s+)|"
    # préambules conversationnels ÉTENDUS : « j'ai une colle pour toi : », « une question qui me trotte : »,
    # « tiens, à propos », « cette histoire de », « excuse-moi de te déranger mais »…
    r"j['’ ]\s*ai\s+une\s+(?:colle|question|devinette|énigme|enigme)(?:\s+pour\s+(?:toi|vous))?\s*[:,]?\s+|"
    r"une\s+question\s+(?:qui\s+me\s+trotte|pour\s+(?:toi|vous))?\s*[:,]?\s+|"
    r"cette\s+histoire\s+de\s+|excuse[- ]?moi\s+de\s+te\s+déranger\s+mais\s+|"
    r"tiens\s*,?\s+(?:à\s+propos\s*,?\s+)?|à\s+propos\s*,?\s+|dis\s+donc\s*,?\s+|"
    r"au\s+fait\s*,?\s+|franchement\s*,?\s+|honnêtement\s*,?\s+|entre\s+nous\s*,?\s+|(?:et\s+)?sinon\s*,?\s+|"
    r"bon(?:\s+alors)?\s*,\s+|alors\s*,\s+|donc\s*,\s+|eh\s+bien\s*,?\s+|"
    r"s['’] ?il\s+te\s+pla[iî]t\s*,?\s+|stp\s*,?\s+|svp\s*,?\s+)+", re.I)
# tags conversationnels de FIN (politesse OU question rhétorique) : « …, non ? », « …, hein ? », « …, tu crois ? »
_DEVOILE_FIN_RE = re.compile(
    r"\s*,?\s*(?:s['’] ?il\s+(?:te|vous)\s+pla[iî]t|stp|svp|merci|non|hein|d['’] ?accord|"
    r"pas\s+vrai|n['’] ?est[- ]?ce\s+pas|tu\s+crois|à\s+ton\s+avis)\s*([?.!]*)\s*$", re.I)
# fillers INSÉRÉS entre un interrogatif « qui a » et le verbe : « qui a BIEN PU écrit », « qui a DONC écrit ».
_DEVOILE_FILLER_RE = re.compile(r"\b(qui\s+a)\s+(?:bien\s+pu|donc|déjà|bien|encore)\s+(?=[a-zà-ÿ])", re.I)


def _devoile(texte: str) -> str:
    """Retire l'enrobage conversationnel (préfixes/préambules + tags de fin + fillers insérés) pour dévoiler la
    QUESTION NUE. Ne renvoie une forme réduite que si elle reste substantielle (≥ 1 mot de 3+ lettres)."""
    nu = _DEVOILE_RE.sub("", texte)
    nu = _DEVOILE_FIN_RE.sub(r"\1", nu)
    nu = _DEVOILE_FILLER_RE.sub(r"\1 ", nu).strip()
    if nu != texte.strip() and re.search(r"[\wà-ÿ]{3,}", nu):
        return nu
    return texte


# ————— RECADRAGE ORAL (fossé de généralisation, mesuré par tests/banc_paraphrases.py) —————
# Le français PARLÉ topicalise (« la Joconde, c'est de qui ? »), clive (« c'est qui qui a écrit… »), postpose
# l'interrogatif (« il est né où, Napoléon ? ») : nos patrons canoniques ratent ces formes. Règles de RÉÉCRITURE
# STRUCTURELLE fermées -> forme canonique, REJOUÉE dans le pipeline (repli sans perte si échec). FAUX=0 : on ne
# fait que réordonner les mots de l'utilisateur ; la réponse vient toujours d'un fait vérifié. L'enchaînement de
# plusieurs règles est géré par la récursion du pipeline (chaque réécriture repasse par (0oral)).
_PREP_DE = {"au": "du", "aux": "des", "en": "de", "à": "de", "a": "de"}   # « au Japon » -> « du Japon »


def _prep_de(m_prep: str) -> str:
    return _PREP_DE.get(m_prep.lower(), "de")


# lexique courant -> canonique (substitution EN PLACE n'importe où dans la phrase, puis rejouée)
_RECADRE_LEX = (
    (re.compile(r"\ba\s+le\s+plus\s+d['’]\s*habitants\b", re.I), "est le plus peuplé"),
    (re.compile(r"\bont\s+le\s+plus\s+d['’]\s*habitants\b", re.I), "sont les plus peuplés"),
    # « ce grand pays qu'est l'Australie » -> « l'Australie » (apposition qualifiante : le GN utile est APRÈS)
    (re.compile(r"\bce(?:tte)?\s+(?:grande?|petite?|beau|belle|fameux|fameuse|c[ée]l[eè]bre|vieux|vieille|"
                r"bon(?:ne)?|magnifique)?\s*[a-zà-ÿ]+\s+qu['’]est\s+", re.I), ""),
    # « quelle pourrait bien être la capitale… » -> « quelle est la capitale… » (modal de politesse)
    (re.compile(r"\b(quel(?:le)?s?)\s+pourrai(?:t|ent)\s+(?:bien\s+)?[êe]tre\b", re.I), r"\1 est"),
    # « qui a (bien) pu écrire X » -> « qui a écrit X » (infinitif modal -> participe, verbes créateurs fermés)
    (re.compile(r"\ba\s+(?:bien\s+)?pu\s+[ée]crire\b", re.I), "a écrit"),
    (re.compile(r"\ba\s+(?:bien\s+)?pu\s+composer\b", re.I), "a composé"),
    (re.compile(r"\ba\s+(?:bien\s+)?pu\s+peindre\b", re.I), "a peint"),
    (re.compile(r"\ba\s+(?:bien\s+)?pu\s+r[ée]aliser\b", re.I), "a réalisé"),
    (re.compile(r"\ba\s+(?:bien\s+)?pu\s+sculpter\b", re.I), "a sculpté"),
    (re.compile(r"\ba\s+(?:bien\s+)?pu\s+inventer\b", re.I), "a inventé"),
    # « l'auteur du roman intitulé 1984 » -> « l'auteur de 1984 » (le type-mot + « intitulé » n'est pas la clé)
    (re.compile(r"\b(?:du|de\s+la|de\s+l['’])\s*(?:roman|livre|film|tableau|morceau|chanson|op[ée]ra|"
                r"oeuvre|œuvre)\s+intitulée?\s+", re.I), "de "),
    # « napoleon 1er » -> « napoleon Ier » (les clés de la base utilisent l'ordinal ROMAIN). Garde : jamais
    # après « le » ni un mois (« le 1er janvier » reste intact).
    (re.compile(r"\b(?!(?:le|janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|"
                r"octobre|novembre|décembre|decembre)\s)([a-zà-ÿ]{3,})\s+1ere?\b", re.I),
     lambda m: "%s Ier" % m.group(1)),
)

_RECADRE_REGLES = (
    # « en quelle année Christophe Colomb a-t-il découvert l'Amérique ? » -> « quand a eu lieu la découverte
    # de Y ». Le sujet est retiré SANS être endossé : la réponse nomme l'ÉVÉNEMENT résolu (« Découverte et
    # exploration de l'Amérique : 1492 »), elle ne confirme pas qui a découvert.
    (re.compile(r"^\s*(?:en\s+quelle\s+ann[ée]+e?|quand)\s+(?:est[- ]ce\s+que\s+)?.+?\s+"
                r"a(?:[\s-]*t[\s-]*(?:il|elle))?\s+d[ée]couvert\s+(.+?)\s*\?*\s*$", re.I),
     lambda m: "quand a eu lieu la découverte de %s ?" % m.group(1)),
    # « combien de gens vivent en France ? » -> « quelle est la population de X » (préambules déjà dévoilés
    # en amont ; .*? tolère un reste d'enrobage). habitent/vivent, en/au/aux/à.
    (re.compile(r".*?\bcombien\s+de\s+(?:gens|personnes|habitants)\s+(?:vivent|habitent)(?:[- ]ils)?\s+"
                r"(?:en|au|aux|a|à)\s+(.+?)\s*\?*\s*$", re.I),
     lambda m: "quelle est la population de %s ?" % m.group(1)),
    # « quel bruit/son fait le cheval ? » -> « quel est le cri de X » (cri_animal : hennissement…)
    (re.compile(r"^\s*quel\s+(?:bruit|son)\s+fait\s+(?:le\s+|la\s+|l['’]\s*|un\s+|une\s+)?(.+?)\s*\?*\s*$", re.I),
     lambda m: "quel est le cri du %s ?" % m.group(1)),
    # « combien mesure le mont Blanc ? » -> « quelle est la hauteur de X » (rejoué sans perte : si la hauteur
    # ne donne rien, l'original continue son chemin).
    (re.compile(r"^\s*combien\s+mesure\s+(?:le\s+|la\s+|l['’]\s*)?(.+?)\s*\?*\s*$", re.I),
     lambda m: "quelle est la hauteur de %s ?" % m.group(1)),
    # « quelle langue parle-t-on à Tokyo / au Japon ? » -> « quelle est la langue de X » (le pont ville->pays
    # ou le lookup pays répond ensuite). Locatif à/au/aux/en couvert.
    # SINGULIER uniquement : « quelLES langUES parle-t-on au Japon ? » (pluriel) veut la LISTE -> laissée
    # au listage inverse existant, pas réécrite.
    (re.compile(r"^\s*quelle\s+langue\s+parle[\s-]*t[\s-]*on\s+(?:a|à|au|aux|en)\s+(.+?)\s*\?*\s*$", re.I),
     lambda m: "quelle est la langue de %s ?" % m.group(1)),
    # clivées redoublées : « qui c'est qui a écrit X » / « c'est qui qui a écrit X » -> « qui a écrit X »
    (re.compile(r"^\s*(?:qui\s+c['’] ?est\s+qui|c['’] ?est\s+qui\s+qui)\s+(.+)$", re.I), lambda m: "qui " + m.group(1)),
    # « c'est qui X ? » -> « qui est X ? » ; « X, c'est qui (déjà) ? » -> « qui est X ? »
    (re.compile(r"^\s*c['’] ?est\s+qui\s+(.+?)\s*\?*\s*$", re.I), lambda m: "qui est %s ?" % m.group(1)),
    (re.compile(r"^\s*(.+?)\s*,?\s+c['’] ?est\s+qui(?:\s+déjà)?\s*\?*\s*$", re.I), lambda m: "qui est %s ?" % m.group(1)),
    # « X, c'est de qui ? » -> « de qui est X ? » (créateur générique)
    (re.compile(r"^\s*(.+?)\s*,?\s+c['’] ?est\s+de\s+qui(?:\s+déjà)?\s*\?*\s*$", re.I), lambda m: "de qui est %s ?" % m.group(1)),
    # DOUBLE topicalisation AVANT la simple (sinon « (.+?), c'est quoi » l'avale) : « et la monnaie, au Japon,
    # c'est quoi ? » -> « c'est quoi la monnaie du Japon ? »
    (re.compile(r"^\s*(?:et\s+)?(l[ae]\s+[\wà-ÿ]+|l['’][\wà-ÿ]+)\s*,\s*(en|au|aux|à)\s+(.+?)\s*,\s*"
                r"c['’] ?est\s+(?:quoi|combien|lequel|laquelle)\s*\?*\s*$", re.I),
     lambda m: "c'est quoi %s %s %s ?" % (m.group(1), _prep_de(m.group(2)), m.group(3))),
    # « c'est quoi (déjà) X » reste canonique ; « X, c'est quoi (déjà) ? » -> « c'est quoi X ? »
    (re.compile(r"^\s*c['’] ?est\s+quoi\s+déjà\s+(.+)$", re.I), lambda m: "c'est quoi " + m.group(1)),
    (re.compile(r"^\s*(.+?)\s*,?\s+c['’] ?est\s+quoi(?:\s+déjà)?\s*\?*\s*$", re.I), lambda m: "c'est quoi %s ?" % m.group(1)),
    # « le PIB de l'Allemagne, c'est combien ? » -> « quel est le PIB de l'Allemagne ? » (valeur chiffrée demandée)
    (re.compile(r"^\s*(.+?)\s*,?\s+c['’] ?est\s+combien\s*\?*\s*$", re.I), lambda m: "quel est %s ?" % m.group(1)),
    # naissance orale : « il est né où, X ? » / « X, il est né où ? » / « où c'est que X est né ? »
    (re.compile(r"^\s*(?:il|elle)\s+est\s+née?\s+où\s*,\s*(.+?)\s*\?*\s*$", re.I), lambda m: "où est né %s ?" % m.group(1)),
    (re.compile(r"^\s*(.+?)\s*,\s*(?:il|elle)\s+est\s+née?\s+où\s*\?*\s*$", re.I), lambda m: "où est né %s ?" % m.group(1)),
    (re.compile(r"^\s*où\s+c['’] ?est\s+qu[e']\s*(.+?)\s+est\s+née?\s*\?*\s*$", re.I), lambda m: "où est né %s ?" % m.group(1)),
    # temporel oral : « X, c'était quand ? » / « c'était quand, X ? » / « c'était en quelle année, X ? »
    (re.compile(r"^\s*(.+?)\s*,?\s+c['’] ?était\s+(?:quand|en\s+quelle\s+année)\s*\?*\s*$", re.I),
     lambda m: "quand a eu lieu %s ?" % m.group(1)),
    (re.compile(r"^\s*c['’] ?était\s+(?:quand|en\s+quelle\s+année)\s*,\s*(.+?)\s*\?*\s*$", re.I),
     lambda m: "quand a eu lieu %s ?" % m.group(1)),
    # durée orale : « elle a duré combien de temps, X ? » / « X a duré combien de temps ? »
    (re.compile(r"^\s*(?:elle|il)\s+a\s+duré\s+combien\s+de\s+temps\s*,\s*(.+?)\s*\?*\s*$", re.I),
     lambda m: "combien de temps a duré %s ?" % m.group(1)),
    (re.compile(r"^\s*(.+?)\s+a\s+duré\s+combien\s+de\s+temps\s*\?*\s*$", re.I),
     lambda m: "combien de temps a duré %s ?" % m.group(1)),
    # calcul postposé : « ça fait combien, EXPR ? » / « EXPR, ça fait combien / ça donne quoi ? »
    (re.compile(r"^\s*ça\s+fait\s+combien\s*,?\s*(.+?)\s*\?*\s*$", re.I), lambda m: "combien font %s ?" % m.group(1)),
    (re.compile(r"^\s*(.+?)\s*,?\s*ça\s+(?:fait\s+combien|donne\s+quoi)\s*\?*\s*$", re.I),
     lambda m: "combien font %s ?" % m.group(1)),
    # localisation orale : « X, c'est dans quel pays / sur quel continent ? » (+ forme postposée)
    (re.compile(r"^\s*(.+?)\s*,?\s+c['’] ?est\s+((?:dans|sur)\s+quel(?:le)?\s+[\wà-ÿ]+)\s*\?*\s*$", re.I),
     lambda m: "%s est %s ?" % (m.group(2), m.group(1))),
    (re.compile(r"^\s*c['’] ?est\s+((?:dans|sur)\s+quel(?:le)?\s+[\wà-ÿ]+)\s*,\s*(.+?)\s*\?*\s*$", re.I),
     lambda m: "%s est %s ?" % (m.group(1), m.group(2))),
    # définition orale : « ça veut dire quoi, X ? » / « X, ça veut dire quoi ? »
    (re.compile(r"^\s*ça\s+veut\s+dire\s+quoi\s*,?\s*(.+?)\s*\?*\s*$", re.I), lambda m: "que veut dire %s ?" % m.group(1)),
    (re.compile(r"^\s*(.+?)\s*,?\s*ça\s+veut\s+dire\s+quoi\s*\?*\s*$", re.I), lambda m: "que veut dire %s ?" % m.group(1)),
    # ontologie orale : « X, c'est bien un Y ? » -> « est-ce que X est un Y ? » ; « est-ce qu'on peut dire
    # que X … » -> « est-ce que X … » (méta-question = la question elle-même)
    (re.compile(r"^\s*(.+?)\s*,\s*c['’] ?est\s+bien\s+(une?)\s+(.+?)\s*\?*\s*$", re.I),
     lambda m: "est-ce que %s est %s %s ?" % (m.group(1), m.group(2), m.group(3))),
    (re.compile(r"^\s*est[- ]?ce\s+qu['’] ?on\s+peut\s+dire\s+qu[e']\s*(.+)$", re.I),
     lambda m: "est-ce que " + m.group(1)),
    # CONFIRMATION générique : « la capitale du Japon, c'est bien Tokyo ? » -> forme à inversion (_oui_non).
    # (Après la règle ontologie « c'est bien UN/UNE Y » qui prime.)
    (re.compile(r"^\s*(.+?)\s*,?\s+c['’] ?est\s+bien\s+(.+?)\s*\?*\s*$", re.I),
     lambda m: "%s est-il %s ?" % (m.group(2), m.group(1))),
    # registre SOUTENU : « en quelle année X s'est-elle déroulée ? » ; « où X a-t-il vu le jour ? »
    (re.compile(r"^\s*en\s+quelle\s+année\s+(.+?)\s+s['’] ?est[- ](?:il|elle)\s+(?:déroulée?|produite?|tenue?)\s*\?*\s*$", re.I),
     lambda m: "quand a eu lieu %s ?" % m.group(1)),
    (re.compile(r"^\s*où\s+(.+?)\s+a[- ]?t[- ]?(?:il|elle)\s+vu\s+le\s+jour\s*\?*\s*$", re.I),
     lambda m: "où est né %s ?" % m.group(1)),
    # habitants indirect : « combien d'habitants a la France ? » -> « quelle est la population de la France ? »
    (re.compile(r"^\s*combien\s+d['’]\s*habitants\s+a\s+(.+?)\s*\?*\s*$", re.I),
     lambda m: "quelle est la population de %s ?" % m.group(1)),
    # localisation postposée : « elle est où, Tokyo ? » / « ça se trouve où, X ? » -> « où se trouve X ? »
    (re.compile(r"^\s*(?:il|elle|ça|ca|c['’] ?est)\s+(?:est\s+où|se\s+trouve\s+où|où)\s*,\s*(.+?)\s*\?*\s*$", re.I),
     lambda m: "où se trouve %s ?" % m.group(1)),
    # œuvres inversées familières : « il a écrit quoi, Orwell ? » -> « qu'a écrit Orwell ? »
    (re.compile(r"^\s*(?:il|elle)\s+a\s+(écrit|composé|peint|réalisé|tourné)\s+quoi\s*,\s*(.+?)\s*\?*\s*$", re.I),
     lambda m: "qu'a %s %s ?" % (m.group(1), m.group(2))),
    # âge à la mort : « quel âge avait X à sa mort ? » -> « à quel âge est mort X ? »
    (re.compile(r"^\s*quel\s+âge\s+avait\s+(.+?)\s+à\s+sa\s+mort\s*\?*\s*$", re.I),
     lambda m: "à quel âge est mort %s ?" % m.group(1)),
    # naissance/décès POSTPOSÉS : « X est né quand ? » / « X est mort où ? » -> forme canonique. Lookahead
    # ANTI-PRONOM : « il est mort quand ? » relève de l'étage pronom (0pro), pas d'un sujet nominal. Sujet
    # JUXTAPOSÉ accepté (« napoleon ier il est né ou ») et « ou » sans accent lu comme « où » (oral/SMS).
    (re.compile(r"^\s*(?!(?:et\s+|puis\s+)?(?:il|elle|on|ça|ca)\s)(.+?)\s+(?:(?:il|elle)\s+)?est\s+"
                r"(née?s?|morte?s?)\s+(quand|où|ou|en\s+quelle\s+année)\s*\?*\s*$", re.I),
     lambda m: "%s est %s %s ?" % ("où" if m.group(3).lower() in ("où", "ou") else "quand", m.group(2), m.group(1))),
    # succession orale : « après X, c'est qui (le roi / la reine / le président) ? »
    (re.compile(r"^\s*après\s+(.+?)\s*,\s*c['’] ?est\s+qui(?:\s+l[ea]\s+[\wà-ÿ]+)?\s*\?*\s*$", re.I),
     lambda m: "qui a succédé à %s ?" % m.group(1)),
    # habitants oral : « combien de gens vivent en X » / « (il) y a combien d'habitants en X » / « X, elle a
    # combien d'habitants ? » -> « population de X »
    (re.compile(r"^\s*combien\s+de\s+(?:gens|personnes)\s+vivent\s+(en|au|aux|à)\s+(.+?)\s*\?*\s*$", re.I),
     lambda m: "quelle est la population %s %s ?" % (_prep_de(m.group(1)), m.group(2))),
    (re.compile(r"^\s*(?:il\s+)?y\s+a\s+combien\s+d['’]\s*habitants\s+(en|au|aux|à)\s+(.+?)\s*\?*\s*$", re.I),
     lambda m: "quelle est la population %s %s ?" % (_prep_de(m.group(1)), m.group(2))),
    (re.compile(r"^\s*(.+?)\s*,?\s+(?:elle|il)\s+a\s+combien\s+d['’]\s*habitants\s*\?*\s*$", re.I),
     lambda m: "quelle est la population de %s ?" % m.group(1)),
    # monnaie orale : « on paie avec quoi au Japon ? » / « avec quelle monnaie paie-t-on en X ? »
    (re.compile(r"^\s*on\s+pa(?:ie|ye)\s+avec\s+quoi\s+(en|au|aux|à)\s+(.+?)\s*\?*\s*$", re.I),
     lambda m: "quelle est la monnaie %s %s ?" % (_prep_de(m.group(1)), m.group(2))),
    (re.compile(r"^\s*avec\s+quelle\s+monnaie\s+pa(?:ie|ye)[- ]?t[- ]?on\s+(en|au|aux|à)\s+(.+?)\s*\?*\s*$", re.I),
     lambda m: "quelle est la monnaie %s %s ?" % (_prep_de(m.group(1)), m.group(2))),
    # relative d'usage : « la monnaie qu'on utilise au Japon » -> « la monnaie du Japon »
    (re.compile(r"^\s*(.*?la\s+[\wà-ÿ]+)\s+qu['’] ?on\s+utilise\s+(en|au|aux|à)\s+(.+)$", re.I),
     lambda m: "%s %s %s" % (m.group(1), _prep_de(m.group(2)), m.group(3))),
    # type interrogé explicite : « quelle ville est la capitale du Japon ? » -> « quelle est la capitale… »
    (re.compile(r"^\s*quel(?:le)?\s+(?:ville|pays|personne|fleuve|rivière|montagne|langue)\s+est\s+(.+)$", re.I),
     lambda m: "quelle est " + m.group(1)),
    # superlatif en tête interrogative : « quel pays d'Afrique est le plus peuplé ? » -> forme nominale canonique
    (re.compile(r"^\s*quel(?:le)?\s+pays\s+(d['’]\s*[\wà-ÿ]+|de\s+[\wà-ÿ' ]+?)\s+est\s+l[ea]\s+plus\s+([\wà-ÿ]+)\s*\?*\s*$", re.I),
     lambda m: "le pays le plus %s %s" % (m.group(2), m.group(1))),
    # comparaison 2 entités orale : « lequel est le plus ADJ : A ou B ? » / « entre A et B, qui est le plus ADJ ? »
    (re.compile(r"^\s*(?:lequel|laquelle|qui)\s+est\s+l[ea]\s+plus\s+([\wà-ÿ]+)\s*[:,]\s*(.+?)\s+ou\s+(.+?)\s*\?*\s*$", re.I),
     lambda m: "%s est-il plus %s que %s ?" % (m.group(2), m.group(1), m.group(3))),
    (re.compile(r"^\s*entre\s+(.+?)\s+et\s+(.+?)\s*,\s*(?:qui|lequel|laquelle)\s+est\s+l[ea]\s+plus\s+([\wà-ÿ]+)\s*\?*\s*$", re.I),
     lambda m: "%s est-il plus %s que %s ?" % (m.group(1), m.group(3), m.group(2))),
    # suspens final : « le pays le plus peuplé d'Afrique, c'est lequel ? » -> la forme nominale nue suffit
    (re.compile(r"^\s*(.+?)\s*,?\s+c['’] ?est\s+(?:lequel|laquelle|lesquels|lesquelles)\s*\?*\s*$", re.I),
     lambda m: "%s ?" % m.group(1)),
)


def _resout_pronom(texte: str, sujet: str) -> str | None:
    """ANAPHORE INTER-TOURS : substitue un pronom nu au dernier SUJET de la conversation — « il est mort
    quand ? » après « où est né Napoléon Ier ? » -> « Napoléon Ier est mort quand ? ». Patrons FERMÉS (pronom
    en tête + prédicat) ; None sinon. FAUX=0 : simple substitution du sujet mémorisé, la réponse reste vérifiée."""
    if not sujet:
        return None
    t = texte.strip()
    m = re.match(r"^\s*(?:et\s+)?(?:il|elle)\s+((?:est|était|a|avait|vit|vivait|habite|habitait|mesure|pèse|"
                 r"s['’] ?appelle)\s+.+)$", t, re.I)
    if m:
        return "%s %s" % (sujet, m.group(1))
    m = re.match(r"^\s*(?:et\s+)?(?:ça|ca|c['’] ?est)\s+se\s+trouve\s+où\s*\?*\s*$", t, re.I) or \
        re.match(r"^\s*(?:et\s+)?(?:ça|ca)\s+(?:est|c['’] ?est)?\s*où\s*\?*\s*$", t, re.I)
    if m:
        return "où se trouve %s ?" % sujet
    m = re.match(r"^\s*parle[- ]?moi\s+(?:de\s+lui|d['’] ?elle|de\s+ça|d['’] ?eux)\s*[.!?]*\s*$", t, re.I)
    if m:
        return "parle-moi de %s" % sujet
    m = re.match(r"^\s*(?:et\s+)?c['’] ?était\s+quand\s*\?*\s*$", t, re.I)
    if m:
        return "quand a eu lieu %s ?" % sujet
    return None


def _recadre_oral(texte: str) -> str | None:
    """Réécrit UNE construction orale vers sa forme canonique (première règle qui matche), ou None. Les
    enchaînements (plusieurs constructions imbriquées) se résolvent par récursion du pipeline."""
    for patron, canon in _RECADRE_LEX:                       # lexique en place (peut cohabiter avec une règle)
        lex = patron.sub(canon, texte)
        if _normalise(lex) != _normalise(texte):
            return lex
    for patron, produit in _RECADRE_REGLES:
        m = patron.match(texte)
        if m:
            reecrit = produit(m).strip()
            if reecrit and _normalise(reecrit) != _normalise(texte):
                return reecrit
            return None
    return None


def _decoupe_relation(expr: str):
    """Sépare « REL de RESTE » au PREMIER connecteur tel que REL (article retiré) soit une TÊTE de relation connue.
    Si le 1er segment n'est pas une relation (il fait partie d'une entité multi-mot), on essaie le connecteur suivant.
    Renvoie (rel, reste) ou None."""
    heads = _attr_heads()
    m = _CONNECTEUR_RE.search(expr)
    while m:
        rel = _strip_article(expr[:m.start()]).strip()
        reste = expr[m.end():].strip()
        if rel and _normalise(rel) in heads and reste:
            return rel, reste
        m = _CONNECTEUR_RE.search(expr, m.start() + 1)
    return None


_DONT_RE = re.compile(
    r"^(?:le\s+|la\s+|l['’]\s*)?([a-zà-ÿ]{3,})\s+dont\s+(?:la\s+|le\s+|l['’]\s*)([a-zà-ÿ]{3,})\s+est\s+(.+)$", re.I)
_OU_TROUVE_RE = re.compile(
    r"^(?:le\s+|la\s+|l['’]\s*)?(pays|ville|continent)\s+(?:o[uù]\s+(?:se\s+(?:trouve|situe)|est(?:\s+situ[ée]+)?)|"
    r"qui\s+abrite|abritant)\s+(.+)$", re.I)


def _resout_relatif(expr: str):
    """Feuille RELATIVE de _resout_noeud : « pays dont la capitale est Tokyo » -> (Japon, [étape]) par lecture
    INVERSE (match UNIQUE exigé — FAUX=0) ; « pays où se trouve la tour Eiffel » -> France par les relations de
    localisation (monument -> ville -> pays si besoin, chaque saut montré). None sinon."""
    m = _DONT_RE.match(expr.strip())
    if m:
        rel2, val = _normalise(m.group(2)), _normalise(_strip_article(m.group(3).strip(" ?.!\"'«»")))
        if rel2 in _attr_heads() and val:
            candidates = [r for r in _relations() if r == rel2 or r.startswith(rel2 + "_")]
            for rel in candidates:
                cell = _charge_reverse(rel).get(val) if _charge_reverse(rel) else None
                if cell and len(cell[1]) == 1:                       # UNIQUE, sinon ambigu -> on n'affirme pas
                    ent = cell[1][0]
                    return _strip_article(ent), ["%s dont %s est %s = %s" % (m.group(1), rel2, cell[0], ent)]
        return None
    m = _OU_TROUVE_RE.match(expr.strip())
    if m:
        typ, ent = _normalise(m.group(1)), _strip_article(m.group(2).strip(" ?.!\"'«»"))
        ne = _normalise(ent)
        if not ne:
            return None
        if typ == "ville":
            cell = _lookup_cell("ville_monument", ent)
            if cell:
                return _strip_article(cell[1]), ["%s est à %s" % (cell[0], cell[1])]
            return None
        rels = _LOC_PAYS_REL if typ == "pays" else _LOC_CONT_REL
        for rel in rels:
            cell = _charge_direct(rel).get(ne) if rel != "pays_ville" else _charge_direct(rel).get(ne)
            if cell:
                return _strip_article(cell[1]), ["%s est dans : %s" % (cell[0], cell[1])]
        if typ == "pays":                                            # monument -> ville -> pays (2 sauts montrés)
            cv = _lookup_cell("ville_monument", ent)
            if cv:
                cp = _charge_direct("pays_ville").get(_normalise(cv[1]))
                if cp:
                    return _strip_article(cp[1]), ["%s est à %s" % (cv[0], cv[1]),
                                                   "%s est %s" % (cp[0], _locatif_pays(cp[1]))]
        return None
    return None


def _resout_noeud(expr: str, ia, verifie, prof: int = 0):
    """Résout une expression nominale en (entité_ou_valeur, [étapes_de_dérivation]). Récursif sur « REL de SUBEXPR ».
    Base : superlatif (« le plus haut sommet de France ») ou entité littérale. FAUX=0 : maillon vérifié ou (None, None)."""
    expr = expr.strip(" ?.!\"'«»")
    if prof > _MAX_SAUTS or not expr:
        return None, None
    dec = _decoupe_relation(expr)
    if dec:
        rel, reste = dec
        sous_val, sous_steps = _resout_noeud(reste, ia, verifie, prof + 1)   # résout le RESTE en une entité vérifiée
        if sous_val is not None:
            # PONT ville->pays AVANT le lookup direct pour un attribut PAYS-CONSTANT d'une VILLE connue :
            # « langue de Tokyo » en direct matche la langue d'une ŒUVRE homonyme (« Tokyo », film -> français,
            # FAUX réel trouvé au test) — quand la ville est dans pays_ville, le sens géographique prime.
            pont = _pont_ville_pays(ia, verifie, rel, sous_val)
            if pont is not None:
                v, pas = pont
                return v, (sous_steps or []) + pas
            v = _val_verifiee(ia, verifie, "%s de %s" % (rel, sous_val), rel_head=rel, entite=sous_val)
            if v is not None:
                return v, (sous_steps or []) + ["%s de %s = %s" % (rel, sous_val, v)]
        v = _val_verifiee(ia, verifie, "%s de %s" % (rel, reste), rel_head=rel, entite=reste)  # RESTE = entité littérale
        if v is not None:
            return v, ["%s de %s = %s" % (rel, reste, v)]
        return None, None
    # base : PROPOSITION RELATIVE résolue en entité — « le pays DONT LA CAPITALE EST Tokyo » -> Japon (lecture
    # inverse, match UNIQUE exigé : FAUX=0) ; « le pays OÙ SE TROUVE la tour Eiffel » -> France (relations de
    # localisation, monument -> ville -> pays si besoin, chaîne montrée).
    rel_leaf = _resout_relatif(expr)
    if rel_leaf:
        return rel_leaf
    # base : feuille superlative -> entité. D'abord l'ARGMAX borné (« le pays le plus peuplé d'Afrique » -> Nigeria,
    # comparaison de faits réels), sinon la relation superlative explicite du moteur, sinon entité littérale.
    arg = _superlatif_argmax(expr)
    if arg:
        return _strip_article(str(arg[0])), [arg[1]]
    try:
        sup = importlib.import_module("resolution").resout_superlatif(expr)
    except Exception:
        sup = None
    if sup:
        return _strip_article(str(sup)), ["%s = %s" % (expr, sup)]
    return _strip_article(expr), []


# Attributs CONSTANTS à l'échelle d'un pays : les demander sur une VILLE se répond via le pays (monnaie de
# Tokyo = monnaie du Japon). La POPULATION n'y est PAS (population de Tokyo ≠ population du Japon). Liste
# FERMÉE — n'y ajouter que des attributs vrais pour TOUT point du pays.
_REL_PAYS_CONST = frozenset(("monnaie", "langue", "continent", "hymne", "devise nationale"))


def _pont_ville_pays(ia, verifie, rel: str, ville) -> tuple | None:
    """PONT ville -> pays pour un attribut pays-constant : (valeur, [étapes]) ou None. FAUX=0 : le pays vient
    de pays_ville (extraction vérifiée SANS nom multi-pays — audit 2026-07-06 : 9998 villes, 0 homonyme) et la
    valeur du fait pays est elle-même vérifiée ; la traversée est MONTRÉE (« Tokyo est au Japon »)."""
    if _normalise(rel) not in _REL_PAYS_CONST:
        return None
    cell = _charge_direct("pays_ville").get(_normalise(str(ville)))
    if not cell:
        return None
    ville_aff, pays = cell
    v = _val_verifiee(ia, verifie, "%s de %s" % (rel, pays), rel_head=rel, entite=pays)
    if v is None:
        return None
    return v, ["%s est %s" % (ville_aff, _locatif_pays(pays)), "%s de %s = %s" % (rel, pays, v)]


def _compose_relations_n(question: str):
    """RAISONNEMENT COMPOSITIONNEL N-SAUTS : « population de la capitale de la France » -> valeur + dérivation
    complète montrée. Exige ≥2 maillons de composition (sinon le lookup simple suffit). FAUX=0 : chaque maillon
    est vérifié ; abstention si un maillon manque. C'est la profondeur EXACTE qu'un LLM ne peut que deviner."""
    q = _HABILLAGE_RE.sub("", question).strip(" ?.!\"'«»")
    if not q:
        return None
    ia, verifie = _charge_ia()
    if not ia:
        return None
    val, steps = _resout_noeud(q, ia, verifie, 0)
    if val is not None and steps and len(steps) >= 2:
        return "%s  (en composant : %s)" % (val, ", puis ".join(steps))
    # ABSTENTION à CHAÎNE PARTIELLE : l'interne résout (« capitale de la France » = Paris, VÉRIFIÉ) mais le
    # maillon EXTERNE manque (« population de Paris » absent de population_ville — trou d'extraction Wikidata).
    # Dire précisément QUEL maillon manque vaut mieux que le générique « rien n'ancre capitale de la France »
    # (factuellement trompeur : l'interne s'ancre très bien). Préfixe structure -> statut HORS conservé.
    dec = _decoupe_relation(q)
    if dec:
        rel, reste = dec
        sous_val, sous_steps = _resout_noeud(reste, ia, verifie, 1)
        if sous_val is not None and sous_steps:
            return ("%s : j'ai composé %s — mais je n'ai pas de fait vérifié « %s de %s » dans mes données. "
                    "Plutôt que d'inventer, je m'abstiens sur ce dernier maillon."
                    % (_MSG_STRUCTURE_PREFIXE, ", puis ".join(sous_steps), rel, sous_val))
    return None


_ENV_INTERNE_RE = re.compile(
    r"(?:la\s+|le\s+|les\s+|l['’]\s*)?([a-zà-ÿ]{3,})\s+"
    r"(?:de\s+la\s+|de\s+l['’]\s*|du\s+|des\s+|d['’]\s*|de\s+)(.+?)\s*[?.!]*\s*$", re.I)
# Préfixe d'ENVELOPPE « réelle » : la question pose une AUTRE question autour du GN composé (« sur quel
# continent se trouve… », « où est né… », « quand est mort… », « qui a écrit… »). Un simple « quelle est la
# capitale de la France » n'en est PAS une (le lookup direct doit la servir).
_ENV_PREFIXE_RE = re.compile(
    r"\b(?:sur|dans|en|a|à)\s+quel(?:le)?s?\s+[a-zà-ÿ]|\b(?:ou|où|quand|qui|comment|combien)\b", re.I)
# GN interne RELATIF en fin de question : « … le pays dont la capitale est Tokyo ? », « … le pays où se
# trouve la tour Eiffel ? » — résolu par la feuille _resout_relatif.
_ENV_RELATIF_RE = re.compile(
    r"((?:le\s+|la\s+|l['’]\s*)?[a-zà-ÿ]{3,}\s+(?:dont\s+(?:la\s+|le\s+|l['’]\s*)[a-zà-ÿ]{3,}\s+est\s+.+?|"
    r"(?:o[uù]\s+(?:se\s+(?:trouve|situe)|est(?:\s+situ[ée]+)?)|qui\s+abrite)\s+.+?))\s*[?.!]*\s*$", re.I)


def _compose_enveloppe(memoire, conv_id, texte: str, pleine: bool):
    """(2b-env) Voir le commentaire du câblage. Résout le GN composé FINAL de la question (« capitale du
    Japon » -> Tokyo, maillon vérifié), substitue, rejoue le pipeline. La substitution et la dérivation du
    rejeu sont toutes deux montrées."""
    interne = reste_interne = None
    m = _ENV_RELATIF_RE.search(texte)                # « … le pays dont la capitale est Tokyo » / « où se trouve … »
    if m:
        interne = reste_interne = m.group(1)
    else:
        m = _ENV_INTERNE_RE.search(texte)
        if not m or _normalise(m.group(1)) not in _attr_heads():
            return None
        interne, reste_interne = "%s de %s" % (m.group(1), m.group(2)), m.group(2)
    ia, verifie = _charge_ia()
    if not ia:
        return None
    val, steps = _resout_noeud(interne, ia, verifie, 0)
    if val is None or not steps:                 # steps vides = feuille littérale, rien de VÉRIFIÉ -> on s'abstient
        return None
    aff = str(val)
    if _normalise(aff) == _normalise(reste_interne.strip()):
        return None
    nouveau = (texte[:m.start()].strip() + " " + aff + " ?").strip()
    if _normalise(nouveau) == _normalise(texte):
        return None
    rep = _rejoue(memoire, conv_id, nouveau, pleine)
    if rep and _utile(rep) and not rep.startswith((_MSG_STRUCTURE_PREFIXE, _MSG_STRUCTURE_COURT_PREFIXE)):
        return "%s  (en composant d'abord : %s)" % (rep, ", puis ".join(steps))
    return None


# Cache du module lourd (chargé au plus une fois, à la première vraie demande en mode IA pleine).
_IA = None
_VERIFIE = None


def _charge_ia():
    """Import PARESSEUX du moteur lourd (lecteur ≈622 Mo). Via importlib : aucune dépendance statique pour les
    outils d'analyse (la gate garde donc ce module 'léger'). Renvoie (module_ia, constante_VERIFIE) ou (None, None)."""
    global _IA, _VERIFIE
    if _IA is None:
        try:
            _IA = importlib.import_module("ia")
            _VERIFIE = importlib.import_module("base_faits").VERIFIE
        except Exception as _e:         # environnement sans lecteur -> on dégrade proprement (pas d'étage 2)
            import traceback
            print("  [Provara] ⚠ moteur de connaissance INDISPONIBLE : %r" % _e, flush=True)
            traceback.print_exc()
            _IA, _VERIFIE = False, None
    return _IA, _VERIFIE


# ————————————————————————————————— REVERSE-LOOKUP « les X d'un pays » —————————————————————————————————
# Le lecteur range certaines relations à l'ENVERS de la question : `pays_riviere` = rivière -> pays (P17). La
# question « quels fleuves en France ? » est donc une requête INVERSE (pays -> ses rivières) que le lookup par
# clé ne sait pas faire. On la sert ICI, de façon SOUND : on lit les données brutes (datasets/lecteur/*.jsonl) et
# on liste les VRAIES entités taguées de ce pays. Aucune invention : entités réelles ou rien. Robuste aux fautes
# de grammaire (« Quelle/Quels ») car on détecte le TYPE (fleuve/lac/…) et le PAYS, pas l'accord.
# (mots-déclencheurs, relation pays_X, libellé, mise-en-garde optionnelle).
# AGNOSTIQUE AU DOMAINE : on ne code AUCUNE relation en dur. Le « registre » des relations = les noms de fichiers
# du lecteur (`pays_riviere`, `pays_musee`, `auteur_oeuvre`, `categorie_element`, …). Une relation « A_B » se lit
# « le B (entité) a pour A (valeur) … » ; la requête INVERSE « quels B en/de <valeur-A> ? » se résout pour
# N'IMPORTE quelle relation. Trois petites tables DATA (pas de logique géo) restent extensibles :
#   • _ALIAS : synonymes utilisateur -> token de relation (« fleuve » -> « riviere »). Idéalement côté moteur un jour.
#   • _LABELS : libellé plus joli pour quelques relations. • _CAVEATS : mises en garde honnêtes.
_GENERIQUES = frozenset("pays code nom prenom type sorte categorie de du des la le les un une en au aux et".split())
_ALIAS = {"fleuve": "riviere", "fleuves": "riviere", "cours": "riviere"}
# Intention de LISTE explicite (verbe/déterminant d'énumération) — autorise l'énumération inverse.
_INTENT_LISTE_INV = frozenset(
    "lesquels lesquelles liste listez cite citez nomme nommez enumere enumerez tous toutes".split())
# Interrogatifs qui, IMMÉDIATEMENT suivis du type, désignent ce type comme l'objet INTERROGÉ (« quel FLEUVE… »
# = liste de fleuves). À distinguer de « composition de l'ÉQUIPE… » où le type est l'objet d'un AUTRE nom.
_INTERRO_TYPE = frozenset("quel quels quelle quelles".split())
# Déterminants SINGULIERS : devant un mot en -s/-x invariable (« LE prix », « LA voix »), le mot n'est PAS un
# pluriel-liste (#90). « les/des/ces/mes/… » (pluriels) en sont absents -> ils laissent le pluriel-liste se déclencher.
_DET_SINGULIER = frozenset("le la l un une du ce cet cette son sa mon ma ton ta notre votre".split())
_LABELS = {"pays_riviere": "Cours d'eau"}
_CAVEATS = {"pays_riviere": "la source ne distingue pas fleuve et rivière"}

import collections as _collections
_REVERSE_CACHE = _collections.OrderedDict()   # relation -> { valeur_norm : (val_affichée, [entités]) } (LRU)
_REVERSE_CACHE_COUT = {}      # relation -> coût approché (octets fichier)
_REVERSE_BUDGET = 20 * 1024 * 1024   # même plafond/logique que _DIRECT (voir _charge_direct) : borne le RSS d'un
                              # serveur long qui construit BEAUCOUP d'index inverses (recherche inverse, œuvres_de…).
_RELATIONS_CACHE = None       # liste des relations (noms de fichiers)
_VOCAB_CACHE = None           # vocabulaire des tokens de type (pour le « did-you-mean »)


def _relations() -> list:
    """Registre des relations connues = fichiers du lecteur. Lu une fois. Domaine-agnostique."""
    global _RELATIONS_CACHE
    if _RELATIONS_CACHE is None:
        try:
            _RELATIONS_CACHE = sorted(f[:-6] for f in os.listdir(_DOSSIER_LECTEUR) if f.endswith(".jsonl"))
        except OSError:
            _RELATIONS_CACHE = []
    return _RELATIONS_CACHE


def _vocab_types() -> set:
    """Tous les mots-types possibles = tokens de noms de relation (+ synonymes connus). Pour le did-you-mean."""
    global _VOCAB_CACHE
    if _VOCAB_CACHE is None:
        v = set(_ALIAS)
        for rel in _relations():
            for tk in rel.split("_"):
                if len(tk) >= 4 and tk not in _GENERIQUES:
                    v.add(tk)
        _VOCAB_CACHE = v
    return _VOCAB_CACHE


def _charge_reverse(relation: str) -> dict:
    """Index inverse VALEUR -> [entités] d'une relation, lu une fois depuis le .jsonl brut puis caché. Générique."""
    cached = _REVERSE_CACHE.get(relation)
    if cached is not None:
        _REVERSE_CACHE.move_to_end(relation)
        return cached
    par_val: dict = {}
    chemin = os.path.join(_DOSSIER_LECTEUR, relation + ".jsonl")
    try:
        cout = os.path.getsize(chemin)
    except OSError:
        cout = 0
    try:
        # GARDE RAM : sur la base COMPLÈTE (~73M faits), certaines relations font des MILLIONS de lignes —
        # matérialiser l'index inverse en dict coûterait des centaines de Mo chez l'utilisateur final (cache
        # sans éviction). Au-delà de 64 Mo on s'abstient (HORS honnête, comme avant) plutôt que saturer la RAM.
        if cout > 64 * 1024 * 1024:
            _REVERSE_CACHE[relation] = {}
            _REVERSE_CACHE_COUT[relation] = 0
            return {}
        with open(chemin, encoding="utf-8") as fh:
            for ligne in fh:
                ligne = ligne.strip()
                if not ligne:
                    continue
                obj = json.loads(ligne)
                if "_relation" in obj:           # en-tête self-describing -> ignorer
                    continue
                ent, val = obj.get("entite"), obj.get("valeur")
                if not ent or not val:
                    continue
                par_val.setdefault(_normalise(val), [val, []])[1].append(str(ent))
    except (OSError, ValueError):
        par_val = {}
    res = {vn: (disp, sorted(set(ents))) for vn, (disp, ents) in par_val.items()}
    _REVERSE_CACHE[relation] = res
    _REVERSE_CACHE_COUT[relation] = cout
    total = sum(_REVERSE_CACHE_COUT.values())
    evince = False
    while total > _REVERSE_BUDGET and len(_REVERSE_CACHE) > 1:
        vieux, _ = _REVERSE_CACHE.popitem(last=False)
        total -= _REVERSE_CACHE_COUT.pop(vieux, 0)
        evince = True
    if evince:
        _malloc_trim()
    return res


_DIRECT_CACHE = _collections.OrderedDict()   # relation -> dict (LRU, voir ci-dessous)
_DIRECT_CACHE_COUT = {}       # relation -> coût approché (octets fichier) de son entrée cachée
_DIRECT_BUDGET = 20 * 1024 * 1024    # PLAFOND (coût = taille .jsonl source) des dicts DIRECT cachés. Un dict
                              # Python pèse ~4-5× son .jsonl (surcoût objets) : 20 Mo de fichiers ≈ ~100 Mo RAM.
                              # Sans borne, un serveur long touchant BEAUCOUP de relations (superlatifs/argmax
                              # variés) montait à +487 Mo (mesuré, 400 relations). Éviction LRU + malloc_trim pour
                              # RENDRE la RAM à l'OS (un free Python seul ne réduit pas le RSS — fragmentation glibc).


def _malloc_trim():
    """Rend au système la mémoire libérée par les évictions (un `del` Python ne réduit pas le RSS : glibc garde
    les arènes). No-op hors glibc/Linux. Sûr : ne touche qu'à la mémoire déjà libre."""
    try:
        import ctypes
        ctypes.CDLL("libc.so.6").malloc_trim(0)
    except Exception:
        pass


def _charge_direct(relation: str) -> dict:
    """Index DIRECT entité -> valeur d'une relation (lu une fois du .jsonl brut). Sert à l'argmax superlatif
    (lire l'attribut de chaque candidat sans passer par le moteur lourd)."""
    cached = _DIRECT_CACHE.get(relation)
    if cached is not None:
        _DIRECT_CACHE.move_to_end(relation)      # LRU : accès récent -> queue (les plus anciens en tête)
        return cached
    d: dict = {}
    chemin = os.path.join(_DOSSIER_LECTEUR, relation + ".jsonl")
    try:
        cout = os.path.getsize(chemin)
    except OSError:
        cout = 0
    try:
        with open(chemin, encoding="utf-8") as fh:
            for ligne in fh:
                ligne = ligne.strip()
                if not ligne:
                    continue
                obj = json.loads(ligne)
                if "_relation" in obj:
                    continue
                e, v = obj.get("entite"), obj.get("valeur")
                if e is not None and v is not None:
                    d[_normalise(e)] = (e, v)
    except (OSError, ValueError):
        d = {}
    _DIRECT_CACHE[relation] = d
    _DIRECT_CACHE_COUT[relation] = cout
    # ÉVICTION LRU par coût : tant que le budget est dépassé, on retire la relation la MOINS récemment utilisée
    # (tête de l'OrderedDict). On garde toujours ≥1 entrée (celle qu'on vient de charger).
    total = sum(_DIRECT_CACHE_COUT.values())
    evince = False
    while total > _DIRECT_BUDGET and len(_DIRECT_CACHE) > 1:
        vieux, _ = _DIRECT_CACHE.popitem(last=False)
        total -= _DIRECT_CACHE_COUT.pop(vieux, 0)
        evince = True
    if evince:                                   # rendre la RAM libérée à l'OS (sinon le RSS ne baisse pas)
        _malloc_trim()
    return d


_STREAM_CACHE: dict = {}      # (relation, entite_norm) -> (affiché, valeur) | None (mémo des lookups streaming)
_STREAM_SEUIL = 4 * 1024 * 1024      # au-delà, on NE charge PAS tout le dict (RAM) : scan ciblé (bytes.find, sortie
                                     # anticipée) à la demande. 4 Mo : les fichiers MOYENS (pays_montagne 15 Mo,
                                     # pays_riviere 14 Mo, date_evenement 12 Mo…) restent en flux — plus léger ET
                                     # souvent plus rapide (early-exit vs chargement complet du dict). Les petits
                                     # (<4 Mo : population_pays, continent…) restent cachés pour les scans répétés
                                     # (superlatif/_membres_attribut, via _charge_direct non concerné par ce seuil).
_TAILLE_FICHIER: dict = {}           # relation -> True (gros) / False (petit) / "absent" — stat() mémoïsé
                                     # (datasets statiques en session ; ~1 ms par stat sur /mnt/c, profilé)
_RELS_PAR_TETE: dict = {}            # tête normalisée -> relations de la famille (borné par les têtes réelles)


def _lookup_cell(relation: str, entite: str):
    """(entité_affichée, valeur_brute) d'UNE entité pour `relation`, sans matérialiser tout l'index si le fichier
    est ÉNORME (annee_naissance_personne = 150 Mo, 3,2 M lignes). Petit fichier -> _charge_direct (caché) ; gros
    fichier -> recherche `bytes.find` au niveau C (lecture par blocs de 8 Mo, RAM transitoire NON retenue) : ~30x
    plus rapide que l'itération ligne-à-ligne Python. Repli scan normalisé si la forme diffère (accents/casse). None."""
    ne = _normalise(entite)
    chemin = os.path.join(_DOSSIER_LECTEUR, relation + ".jsonl")
    # taille MÉMOÏSÉE : les datasets sont statiques en session, et un stat() sur /mnt/c coûte ~1 ms —
    # payé par relation à CHAQUE appel, c'était l'atome dominant de « point de fusion du fer » (19 ms,
    # profilé 2026-07-08).
    gros = _TAILLE_FICHIER.get(relation)
    if gros is None:
        try:
            gros = os.path.getsize(chemin) > _STREAM_SEUIL
        except OSError:
            gros = "absent"
        _TAILLE_FICHIER[relation] = gros
    if gros == "absent":
        return None
    if not gros:
        return _quarantaine_cell(relation, _charge_direct(relation).get(ne))
    clef = (relation, ne)
    if clef in _STREAM_CACHE:
        return _quarantaine_cell(relation, _STREAM_CACHE[clef])
    trouve = _scan_bytes(chemin, ne, entite)
    if len(_STREAM_CACHE) >= 16384:              # BORNE RAM (mandat 2026-07-08) : cache pur -> purge simple,
        _STREAM_CACHE.clear()                    # jamais de croissance illimitée sur les longues sessions
    _STREAM_CACHE[clef] = trouve
    return _quarantaine_cell(relation, trouve)


def _quarantaine_cell(relation: str, cell):
    """QUARANTAINE FAUX=0 (vécu 2026-07-08, miroir de lecteur.Lecteur.cherche) : les nationalités JOINTES
    « X et Y » du dataset livré sont TRONQUÉES à 2 par fréquence de corpus (Messi -> « Italie et Espagne »,
    SANS l'Argentine !) — une liste incomplète servie comme nationalité = faux par omission -> None (abstention).
    Protège fiches personne et faits ciblés jusqu'à la ré-ingestion (ingere_celebres P27 joinmax=1)."""
    if cell is not None and relation == "nationalite_personne" and " et " in str(cell[1]):
        return None
    return cell


def _scan_bytes(chemin: str, ne: str, entite: str):
    """Cherche l'entité normalisée `ne` dans un gros .jsonl, en UN SEUL scan par blocs de 8 Mo, recherche
    INSENSIBLE À LA CASSE au niveau C (bloc.lower() puis `besoin in`). On ne parse QUE les lignes candidates. RAM
    plate (blocs non retenus). (affiché, valeur) | None. Beaucoup plus rapide que l'itération ligne-à-ligne Python."""
    besoin = ('"entite": "%s"' % entite).encode("utf-8").lower()
    reste = b""
    try:
        with open(chemin, "rb") as fh:
            while True:
                bloc = fh.read(8 << 20)
                if not bloc:
                    lignes = [reste] if reste else []
                else:
                    bloc = reste + bloc
                    coupe = bloc.rfind(b"\n")
                    if coupe < 0:
                        reste = bloc
                        continue
                    tete, reste = bloc[:coupe], bloc[coupe + 1:]
                    if besoin not in tete.lower():        # aucun candidat -> on saute le parse (C-speed)
                        continue
                    lignes = tete.split(b"\n")
                for brut in lignes:
                    if besoin not in brut.lower():
                        continue
                    s = brut.strip()
                    if not s or b'"_relation"' in s:
                        continue
                    try:
                        obj = json.loads(s.decode("utf-8"))
                    except (ValueError, UnicodeDecodeError):
                        continue
                    e, v = obj.get("entite"), obj.get("valeur")
                    if e is not None and v is not None and _normalise(e) == ne:
                        return (str(e), v)
                if not bloc:
                    break
    except OSError:
        return None
    return None


def _lookup_valeur(relation: str, entite: str):
    """Valeur brute d'UNE entité (RAM-sûr sur gros fichiers, cf. _lookup_cell). None si absente."""
    cell = _lookup_cell(relation, entite)
    return cell[1] if cell else None


# Adjectif superlatif -> relations d'attribut candidates (1re existante retenue). Domaine-extensible.
_ADJ_ATTR = {
    "peuple": ("population_pays",), "peuplee": ("population_pays",), "peuples": ("population_pays",),
    "peuplees": ("population_pays",),
    # NB : la relation réelle des données (échantillon ET base complète) est « superficie » (mledoze, km²) ;
    # « superficie_pays » est gardée en tête au cas où une base future l'introduirait.
    "grand": ("superficie_pays", "superficie", "population_pays"),
    "grande": ("superficie_pays", "superficie", "population_pays"),
    "grands": ("superficie_pays", "superficie", "population_pays"),
    "grandes": ("superficie_pays", "superficie", "population_pays"),
    "vaste": ("superficie_pays", "superficie"), "vastes": ("superficie_pays", "superficie"),
    "etendu": ("superficie_pays", "superficie"), "etendue": ("superficie_pays", "superficie"),
    "etendus": ("superficie_pays", "superficie"),
    "petit": ("superficie_pays", "superficie"), "petite": ("superficie_pays", "superficie"),
    "petits": ("superficie_pays", "superficie"), "petites": ("superficie_pays", "superficie"),
    "riche": ("pib_pays", "pib_par_habitant_pays"), "riches": ("pib_pays", "pib_par_habitant_pays"),
    # AU-DELÀ DES PAYS (base complète) : sommets/montagnes par ALTITUDE, fleuves par LONGUEUR. Le résolveur par
    # paire (_attr_pour_paire) choisit, dans la famille, la relation qui contient RÉELLEMENT les deux entités —
    # « l'Everest est-il plus haut que le mont Blanc ? », « la Loire est-elle plus longue que la Seine ? ».
    "haut": ("altitude_montagne", "altitude_sommet", "altitude_col", "hauteur_montagne", "altitude_ville"),
    "haute": ("altitude_montagne", "altitude_sommet", "altitude_col", "hauteur_montagne", "altitude_ville"),
    "hauts": ("altitude_montagne", "altitude_sommet", "altitude_col"),
    "hautes": ("altitude_montagne", "altitude_sommet", "altitude_col"),
    "eleve": ("altitude_montagne", "altitude_sommet", "altitude_col", "altitude_ville"),
    "elevee": ("altitude_montagne", "altitude_sommet", "altitude_col", "altitude_ville"),
    "long": ("longueur_fleuve", "longueur_cours_eau", "longueur_pont", "longueur_ligne_ferroviaire"),
    "longue": ("longueur_fleuve", "longueur_cours_eau", "longueur_pont", "longueur_ligne_ferroviaire"),
    "longs": ("longueur_fleuve", "longueur_cours_eau"), "longues": ("longueur_fleuve", "longueur_cours_eau"),
}
# relations d'APPARTENANCE candidates par type d'entité (zone -> membres). 1re dont le reverse contient la zone.
_APPARTENANCE = {"pays": ("continent", "region_pays"), "ville": ("pays_ville",), "montagne": ("continent_montagne",)}
# Types dont l'ÉNUMÉRATION par zone est COMPLÈTE -> un superlatif « le plus X » y est SAIN (FAUX=0). Les autres
# types (montagne/ville) ont un membership troué (extrêmes manquants) : le comptage/filtre les liste en disant
# « dans mes données », mais un superlatif AFFIRMÉ y serait faux -> _superlatif_argmax s'y abstient.
_SUPERLAT_TYPES_SÛRS = frozenset({"pays"})
# marqueurs de ZONE GLOBALE : « le pays le plus peuplé DU MONDE » -> argmax sur TOUS les pays (ensemble complet).
_ZONES_GLOBALES = frozenset("monde terre planete univers total globe".split())


def _nombre(v):
    """Extrait un flottant d'une valeur brute (« 43844111 », « 1 234,5 » -> 43844111.0 / 1234.5), ou None."""
    try:
        s = re.sub(r"[^\d,.-]", "", str(v)).replace(" ", "")
        if s.count(",") == 1 and s.count(".") == 0:
            s = s.replace(",", ".")
        else:
            s = s.replace(",", "")
        return float(s)
    except (ValueError, TypeError):
        return None


def _membres_attribut(typ: str, zone: str, adj: str):
    """(paires triées desc [(entité_affichée, valeur_num)], relation_attribut) pour les membres du TYPE dans la ZONE,
    évalués sur l'attribut de l'ADJECTIF. Mutualisé par le superlatif (top-1), le classement (top-N) et le tri.
    FAUX=0 : compare des faits réels sur un ensemble ÉNUMÉRÉ (complet -> exact)."""
    attr_rel = next((r for r in _ADJ_ATTR.get(adj, ()) if _charge_direct(r)), None)
    if not attr_rel:
        return None, None
    membres = None
    # ZONE GLOBALE (« du monde », « au monde », « de la planète ») : l'ensemble est TOUS les membres du type —
    # pour un pays, l' énumération est complète (attribut couvrant tous les pays) donc le superlatif reste SOUND.
    # Gardé aux types sûrs (_SUPERLAT_TYPES_SÛRS) : on n'affirme un extrême GLOBAL que sur un ensemble complet.
    if _normalise(zone) in _ZONES_GLOBALES:
        if typ not in _SUPERLAT_TYPES_SÛRS:
            return None, None
        attr = _charge_direct(attr_rel)
        paires = sorted(((c[0], _nombre(c[1])) for c in attr.values() if _nombre(c[1]) is not None),
                        key=lambda p: -p[1])
        return paires, attr_rel
    for rel_app in _APPARTENANCE.get(typ, ()):
        rev = _charge_reverse(rel_app)
        hit = rev.get(_normalise(zone))
        if hit and hit[1]:
            membres = hit[1]
            break
    if not membres:
        return None, None
    attr = _charge_direct(attr_rel)
    paires = []
    for ent in membres:
        cell = attr.get(_normalise(ent))
        if cell:
            x = _nombre(cell[1])
            if x is not None:
                paires.append((cell[0], x))
    paires.sort(key=lambda p: -p[1])
    return paires, attr_rel


_ANALOGIE_RE = re.compile(
    r"^\s*(.+?)\s+est\s+(?:aux?\s+|[àa]\s+(?:la\s+|le\s+|les\s+|l['’])?)(.+?)\s+ce\s+que\s+(.+?)\s+"
    r"est\s+(?:aux?|[àa])\s*(?:quoi|qui)?\s*\??\s*$", re.I)
# relations candidates pour l'analogie (fonctionnelles, un-à-un fréquentes). Cherchées dans cet ordre.
# NB : noms VÉRIFIÉS contre les données (2026-07-04) — « hymne » n'existait pas (réel : hymne_national) ;
# president_pays / plus_grande_ville / monnaie_pays n'ont pas (encore) de dataset : gardés en queue comme
# intentions, ils ne coûtent rien (candidat jamais chargé) et se câbleront seuls si une base future les fournit.
_REL_ANALOGIE = ("capitale", "monnaie", "continent", "langue_officielle", "hymne_national", "gentile",
                 "point_culminant", "president_pays", "plus_grande_ville", "monnaie_pays")


def _cap_analogie(texte: str):
    """RAISONNEMENT ANALOGIQUE : « Paris est à la France ce que Berlin est à … ? » -> la machine DÉCOUVRE la relation
    qui relie les deux premiers (capitale) et la TRANSFÈRE au troisième. FAUX=0 : la relation est un fait vérifié et
    la réponse aussi ; sinon None. C'est une correspondance de STRUCTURE, pas une devinette."""
    m = _ANALOGIE_RE.match(texte)
    if not m:
        return None
    a, b, c = (_strip_article(m.group(i).strip()) for i in (1, 2, 3))
    na, nb, nc = _normalise(a), _normalise(b), _normalise(c)
    if not (na and nb and nc):
        return None
    for rel in _REL_ANALOGIE:
        direct = _charge_direct(rel)
        lbl = rel.replace("_", " ")
        # sens B->A (« rel de B = A », ex. capitale de France = Paris) : transférer à C via le reverse (qui a rel=C ?)
        cell = direct.get(nb)
        if cell and _normalise(cell[1]) == na:
            hit = _charge_reverse(rel).get(nc)
            if hit and hit[1] and len(hit[1]) == 1:
                rep = hit[1][0]
                return "%s — %s est à %s ce que %s est à %s (relation : %s)." % (rep, c, rep, a, b, lbl)
        # sens A->B (« rel de A = B ») : transférer à C par lookup direct (rel de C = ?)
        cell = direct.get(na)
        if cell and _normalise(cell[1]) == nb:
            cellc = direct.get(nc)
            if cellc and cellc[1]:
                return "%s — %s est à %s ce que %s est à %s (relation : %s)." % (cellc[1], c, cellc[1], a, b, lbl)
    return None


_DATE_RELS_CACHE = None


def _relations_date() -> list:
    """Relations de DATES de la base (annee_*/date_*), les plus courantes d'abord. Pour situer un événement dans le temps."""
    global _DATE_RELS_CACHE
    if _DATE_RELS_CACHE is None:
        prio = ["annee_debut_bataille", "annee_debut_guerre", "annee_debut_siege", "date_evenement",
                "annee_fondation_pays", "annee_signature_traite", "annee_debut_regne", "annee_debut_revolution",
                "annee_naissance", "annee_debut_operation_militaire", "annee_fondation_organisation_internationale"]
        try:
            rels = [f[:-6] for f in os.listdir(_DOSSIER_LECTEUR)
                    if f.endswith(".jsonl") and (f.startswith("annee_") or f.startswith("date_") or f.startswith("an_"))]
        except OSError:
            rels = []
        # PERF : les dates de PERSONNES (annee_naissance_personne 151 Mo, annee_deces_personne 79 Mo) sont servies
        # par les caps personnes (_cap_age, _cap_fait_personne) et n'ont RIEN à faire dans le temporel d'ÉVÉNEMENTS.
        # Sans cette exclusion, un événement absent des petites relations (« bataille de Waterloo ») faisait scanner
        # ces 2 gros fichiers -> ~17 s. On les retire du scan générique de dates.
        _EXCLUS = {"annee_naissance_personne", "annee_deces_personne"}
        rels = [r for r in rels if r not in _EXCLUS]
        _DATE_RELS_CACHE = [r for r in prio if r in rels] + [r for r in rels if r not in prio]
    return _DATE_RELS_CACHE


def _variantes_elision(nom: str) -> list:
    """Variantes d'ÉLISION d'un nom d'événement : les clés réelles des datasets élident devant voyelle/h
    (« bataille d'Hastings ») là où la question dit « de Hastings » — et la guérison/normalisation perd
    l'apostrophe (« bataille d hastings »). Sans ces variantes, le lookup STREAMING (texte brut) rate la clé
    et la question file vers la cascade lourde (qui répondait « Battle », la VILLE du lieu de la bataille)."""
    regles = (
        (r"\bde\s+([aeiouyhàâäéèêëîïôöùûü])", r"d'\1"),        # de Hastings -> d'Hastings
        (r"\bd\s+([aeiouyhàâäéèêëîïôöùûü])", r"d'\1"),         # d hastings -> d'hastings (apostrophe perdue)
        (r"\bl\s+([aeiouyhàâäéèêëîïôöùûü])", r"l'\1"),         # l amerique -> l'amerique
        (r"\bd['’]\s*(?=[A-ZÀ-Ü])", "de "),                     # d'Hastings -> de Hastings
        # libellé Wikidata composé : « découverte de l'Amérique » est stocké « découverte ET EXPLORATION de … »
        (r"^d[ée]couverte\s+de\s+", "découverte et exploration de "),
    )
    v = [nom]
    for pat, rempl in regles:                                   # application CUMULATIVE : les règles se composent
        for base in list(v):
            n = re.sub(pat, rempl, base, flags=re.I)
            if n not in v:
                v.append(n)
    return v[:8]                                                # borne dure (coût d'un miss = 1 scan par variante)


def _annee_de(entite: str):
    """Année associée à un événement/entité, cherchée dans les relations de dates (1re trouvée). (annee:int, affiché)
    ou (None, None). RAM-sûr : via _lookup_cell -> les gros fichiers de dates (annee_naissance_personne 150 Mo,
    annee_deces 79 Mo) sont lus en STREAMING ciblé, jamais matérialisés en dict de centaines de Mo.
    NOM NU CÉLÈBRE (« Marignan ») : l'ÉVÉNEMENT du même nom (« bataille de Marignan », date_evenement) prime sur
    un homonyme obscur d'une autre relation (« Marignan » -> annee_dissolution 1790 d'une commune). Le nom résolu
    est AFFICHÉ en entier (« bataille de Marignan ») : l'utilisateur voit quel sens a été retenu — sound."""
    if len(entite.split()) <= 2:                          # nom court -> tenter l'événement explicite d'abord
        for tete, rels in (("bataille de %s", ("annee_debut_bataille", "date_evenement")),
                           ("bataille d'%s", ("annee_debut_bataille", "date_evenement")),
                           ("guerre de %s", ("annee_debut_guerre", "date_evenement")),
                           ("siège de %s", ("date_evenement",)),
                           ("traité de %s", ("date_evenement",))):
            for rel in rels:
                cell = _lookup_cell(rel, tete % entite)
                if cell:
                    a = _nombre(cell[1])
                    if a is not None:
                        return int(a), cell[0]
    for rel in _relations_date():
        for var in _variantes_elision(entite):
            cell = _lookup_cell(rel, var)
            if cell:
                a = _nombre(cell[1])
                if a is not None:
                    return int(a), cell[0]
    return None, None


_TEMPO_AVANT_RE = re.compile(
    r"^\s*(?:est[- ]ce\s+que\s+)?(.+?)\s+(?:a[- ]t[- ](?:il|elle)|est[- ](?:il|elle)|a|est)\s+"
    r"(?:eu\s+lieu\s+|commenc[ée]+e?\s+|d[ée]but[ée]+e?\s+)?(avant|apr[eè]s)\s+(.+?)\s*\??\s*$", re.I)
_TEMPO_ENTRE_RE = re.compile(
    r"(?:quel|qu[e'’]?\s*est[- ]ce\s+qui|lequel|laquelle|qui)\b[^?]*?"
    r"(plus\s+ancien\w*|plus\s+r[ée]cent\w*|plus\s+vieux|plus\s+vieille|premier|premi[èe]re|"
    r"arriv[ée]+\s+(?:en\s+)?premi|en\s+premier|le\s+plus\s+t[ôo]t|le\s+plus\s+tard)\b[^?]*?"
    r"(?:entre|de|parmi|:)\s+(.+?)\s+(?:et|ou)\s+(.+?)\s*\??\s*$", re.I)


def _cap_temporel(texte: str):
    """RAISONNEMENT TEMPOREL : « quel est le plus ancien entre la bataille de Marignan et Verdun ? », « Marignan
    a-t-elle eu lieu avant Verdun ? ». Compare des DATES vérifiées et montre les années. FAUX=0 : jamais de verdict
    sans les deux dates ; on énonce le vrai ordre si l'assertion est fausse."""
    _maj = lambda s: (s[:1].upper() + s[1:]) if s else s
    m = _TEMPO_AVANT_RE.match(texte)
    if m:
        x, rel_mot, y = _strip_article(m.group(1).strip()), _normalise(m.group(2)), _strip_article(m.group(3).strip())
        ax, afx = _annee_de(x)
        ay, afy = _annee_de(y)
        if ax is None or ay is None:
            return None
        veut_avant = rel_mot.startswith("avant")
        vrai = (ax < ay) if veut_avant else (ax > ay)
        rel_txt = "avant" if veut_avant else "après"
        inv_txt = "après" if veut_avant else "avant"
        if ax == ay:
            return "Les deux datent de %d — c'est la même année." % ax
        if vrai:
            return "Oui — %s (%d) est %s %s (%d)." % (_maj(afx), ax, rel_txt, afy, ay)
        return "Non — %s (%d) est en fait %s %s (%d)." % (_maj(afx), ax, inv_txt, afy, ay)
    m = _TEMPO_ENTRE_RE.search(texte)
    if not m:
        return None
    critere, x, y = _normalise(m.group(1)), _strip_article(m.group(2).strip()), _strip_article(m.group(3).strip())
    ax, afx = _annee_de(x)
    ay, afy = _annee_de(y)
    if ax is None or ay is None:
        return None
    veut_ancien = ("ancien" in critere or "vieu" in critere or "premi" in critere or "tot" in critere)
    if ax == ay:
        return "Les deux datent de %d — c'est la même année." % ax
    gagnant = (afx, ax, afy, ay) if ((ax < ay) == veut_ancien) else (afy, ay, afx, ax)
    g_aff, g_an, p_aff, p_an = gagnant
    qualif = "le plus ancien" if veut_ancien else "le plus récent"
    return "%s (%d) — c'est %s (%s date de %d)." % (_maj(g_aff), g_an, qualif, p_aff, p_an)


# DATE d'un événement : « quand a eu lieu la bataille de Marignan ? » -> 1515. « commencé/débuté » -> année de
# début, « terminé/fini » -> année de fin (familles appariées), sinon l'année principale (_annee_de). FAUX=0.
_DATE_EVT_RE = re.compile(
    r"^\s*(?:quand\s+(?:a\s+eu\s+lieu\s+|a\s+commenc[ée]\s+|a\s+d[ée]but[ée]\s+|s['’ ]est\s+termin[ée]e?\s+|"
    r"s['’]est\s+fini\w*\s+|a\s+pris\s+fin\s+|s['’]est\s+d[ée]roul[ée]e?\s+|a\s+eu\s+lieu\s+)"
    r"|en\s+quelle\s+ann[ée]+e?\s+(?:a\s+eu\s+lieu\s+|a\s+commenc[ée]\s+|s['’ ]est\s+termin[ée]e?\s+|"
    r"(?:a\s+)?(?:d[ée]but[ée]|fini|eu\s+lieu)\s+|est\s+)"
    r"|de\s+quand\s+date\s+)(.+?)\s*\??\s*$", re.I)


# VERBE -> RELATION de date : « est TOMBÉ le mur de Berlin » = annee_dissolution (1989), « a été CONSTRUIT »
# = annee_construction_edifice (1961). Sans ce routage, _annee_de rend la PREMIÈRE date trouvée (l'ordre des
# relations déciderait entre 1961 et 1989 — un coup de dés, pas un fait).
_DATE_VERBE_RE = re.compile(
    r"^\s*(?:quand|en\s+quelle\s+ann[ée]+e?)\s+(?:est\s+(tomb[ée]|chut[ée]|sorti[es]?|paru[es]?)|a\s+(?:[ée]t[ée]\s+)?"
    r"(construite?|[ée]rig[ée]e?|b[âa]tie?|d[ée]truite?|d[ée]molie?|dissoute?|sign[ée]e?|publi[ée]e?s?))\s+"
    r"(?:le\s+film\s+|le\s+roman\s+|le\s+livre\s+|l['’]album\s+|le\s+|la\s+|les\s+|l['’]\s*)?(.+?)\s*\??\s*$", re.I)
# ⚠ ROUTAGE PAR VERBE, jamais « première date trouvée » : « publié » ne touche QUE annee_publication_oeuvre —
# annee_creation_oeuvre_art contient des ŒUVRES D'ART homonymes (« Les Misérables » (tableau, 1900) ≠ le roman
# de 1862 : servir 1900 pour « quand a été publié Les Misérables » serait un FAUX). « sorti » (films) passe
# par oeuvre_art (Avatar → 2009) puis publication en repli.
_DATE_VERBE_RELS = {"tomb": ("annee_dissolution",), "chut": ("annee_dissolution",),
                    "sign": ("annee_signature_traite", "date_evenement"),
                    "detruit": ("annee_dissolution", "annee_demolition"), "demoli": ("annee_demolition",),
                    "dissou": ("annee_dissolution",),
                    "construit": ("annee_construction_edifice",), "erig": ("annee_construction_edifice",),
                    "bati": ("annee_construction_edifice",),
                    "sorti": ("annee_creation_oeuvre_art", "annee_publication_oeuvre"),
                    "paru": ("annee_publication_oeuvre",), "publi": ("annee_publication_oeuvre",)}


def _cap_date_evenement(texte: str):
    """DATE d'un événement : « quand a eu lieu la bataille de Marignan ? » -> « 1515 ». « quand a commencé la
    guerre de Cent Ans ? » -> année de début ; « quand s'est terminée … ? » -> année de fin. FAUX=0 : année
    vérifiée ou None ; av. J.-C. géré. Verbes SPÉCIFIQUES routés vers LEUR relation (« est tombé le mur de
    Berlin » -> annee_dissolution 1989, jamais l'année de construction 1961)."""
    mv = _DATE_VERBE_RE.match(texte.strip())
    if mv:
        verbe = _normalise(mv.group(1) or mv.group(2) or "")
        ent = mv.group(3).strip()
        rels = next((r for pref, r in _DATE_VERBE_RELS.items() if verbe.startswith(pref)), None)
        if rels and len(ent) >= 3:
            for rel in rels:
                for var in _variantes_elision(ent):
                    cell = _lookup_cell(rel, var)
                    if cell:
                        a = _nombre(cell[1])
                        if a is not None:
                            lib = {"annee_dissolution": "est tombé en", "annee_demolition": "a été démoli en",
                                   "annee_signature_traite": "a été signé en",
                                   "annee_construction_edifice": "a été construit en",
                                   "annee_creation_oeuvre_art": "est sorti en",
                                   "annee_publication_oeuvre": "a été publié en"}.get(rel, ":")
                            return "%s %s %d." % (cell[0][:1].upper() + cell[0][1:], lib, int(a))
        return None
    m = _DATE_EVT_RE.match(texte.strip())
    if not m:
        return None
    ent = _strip_article(m.group(1).strip())
    if not ent or len(ent) < 3:
        return None
    qn = _normalise(texte)
    borne = lambda a: ("%d av. J.-C." % -a) if a < 0 else "%d" % a
    trouve = _duree_de(ent)                               # (debut, fin, affiché, fam) si événement borné
    if trouve and ("commenc" in qn or "debut" in qn):
        d, _f, aff, _fam = trouve
        return "%s a commencé en %s." % (aff[:1].upper() + aff[1:], borne(d))
    if trouve and ("termin" in qn or "fini" in qn or "pris fin" in qn):
        _d, f, aff, _fam = trouve
        return "%s s'est terminé%s en %s." % (aff[:1].upper() + aff[1:], "e" if _fem_evt(aff) else "", borne(f))
    an, aff = _annee_de(ent)
    if an is None:
        return None
    return "%s : %s." % (aff[:1].upper() + aff[1:], borne(an))


def _fem_evt(nom: str) -> bool:
    """L'événement est-il désigné par un mot féminin (bataille, guerre, révolution…) pour l'accord « terminée » ?"""
    return bool(re.match(r"^(?:(?:premi[eè]re|seconde|deuxi[eè]me|grande)\s+)?"
                         r"(?:bataille|guerre|r[ée]volution|campagne|op[ée]ration|croisade|conqu[êe]te|dynastie)\b",
                         _normalise(nom)))


# TEMPOREL N-ÉVÉNEMENTS : « quel est le plus ancien entre Marignan, Verdun et Waterloo ? ». Argmin/argmax sur les
# DATES d'une liste explicite (≥3). Le 2-événements reste géré par _cap_temporel. FAUX=0 : dates vérifiées.
_TEMPON_RE = re.compile(
    # préfixe interrogatif OPTIONNEL : « LE PLUS ANCIEN entre X, Y et Z ? » (forme courte) marche aussi —
    # sinon la question filait au multi-questions qui découpait l'énumération sur les virgules (bruit).
    r"^\s*(?:(?:quel|qu[e'’]?\s*est[- ]ce\s+qui|lequel|laquelle|qui)\b[^?]*?)?"
    r"(?:le\s+|la\s+)?(plus\s+ancien\w*|plus\s+r[ée]cent\w*|plus\s+vieux|plus\s+vieille|premier|premi[èe]re|"
    r"le\s+plus\s+t[ôo]t|le\s+plus\s+tard|dernier|derni[èe]re)\b[^?]*?"
    r"(?:entre|parmi|de)\s+(.+?)\s*\??\s*$", re.I)


def _cap_temporel_nway(texte: str):
    """ARGMIN/ARGMAX sur les DATES d'une LISTE explicite d'événements (« le plus ancien entre Marignan, Verdun et
    Waterloo »). FAUX=0 : dates vérifiées ; None si < 2 événements datés. Montre l'année gagnante et le décompte."""
    m = _TEMPON_RE.match(texte.strip())
    if not m:
        return None
    critere = _normalise(m.group(1))
    ents = [_strip_article(e.strip()) for e in re.split(r"\s*,\s*|\s+et\s+|\s+ou\s+", m.group(2)) if e.strip()]
    ents = [e for e in ents if e and len(e) >= 2]
    if len(ents) < 3:                                # 2 -> laissé à _cap_temporel (message dédié)
        return None
    dates = [(e,) + _annee_de(e) for e in ents]
    ok = [(e, a, aff) for (e, a, aff) in dates if a is not None]
    if len(ok) < 2:
        return None
    veut_ancien = ("ancien" in critere or "vieu" in critere or "premi" in critere or "tot" in critere)
    gagnant = (min if veut_ancien else max)(ok, key=lambda t: t[1])
    qualif = "le plus ancien" if veut_ancien else "le plus récent"
    manquants = len(ents) - len(ok)
    note = "" if manquants == 0 else " (%d sans date, exclu%s)" % (manquants, "s" if manquants > 1 else "")
    aff = gagnant[2]
    return "%s (%d) — %s des %d datés%s." % (aff[:1].upper() + aff[1:], gagnant[1], qualif, len(ok), note)


# ÉCART TEMPOREL entre DEUX événements = |année(X) − année(Y)|. « combien d'années séparent Marignan et Waterloo ? »
# -> « 300 ans (1515 et 1815) ». FAUX=0 : deux dates vérifiées ; None si l'une manque ; les deux années montrées.
_ECART_TEMPO_RE = re.compile(
    r"^\s*(?:combien\s+d['’]?\s*ann[ée]+es?\s+s[ée]parent\s+"
    r"|combien\s+de\s+temps\s+(?:s['’]?est\s+[ée]coul[ée]+\s+|(?:il\s+)?y\s+a[- ]t[- ]il\s+)?"
    r"(?:entre|s[ée]pare)\s+"
    r"|quel\s+(?:est\s+l['’]?\s*)?[ée]cart\s+(?:de\s+temps\s+|d['’]?\s*ann[ée]+es?\s+)?"
    r"(?:temporel\s+)?entre\s+)"
    r"(.+?)\s+(?:et|avec)\s+(.+?)\s*\??\s*$", re.I)


def _cap_ecart_temporel(texte: str):
    """ÉCART EXACT entre deux événements datés : « combien d'années séparent la bataille de Marignan et celle de
    Waterloo ? » -> « 300 ans (1515 et 1815) ». |année(X) − année(Y)|. FAUX=0 : None si une date manque ; av. J.-C.
    géré (années négatives) ; les deux années montrées."""
    m = _ECART_TEMPO_RE.match(texte.strip())
    if not m:
        return None
    x, y = _strip_article(m.group(1).strip()), _strip_article(m.group(2).strip())
    ax, afx = _annee_de(x)
    ay, afy = _annee_de(y)
    if ax is None or ay is None:
        return None
    borne = lambda a: ("%d av. J.-C." % -a) if a < 0 else "%d" % a
    maj = lambda s: (s[:1].upper() + s[1:]) if s else s      # 1re lettre seulement (garde « Marignan », pas « marignan »)
    ecart = abs(ax - ay)
    if ecart == 0:
        return "%s et %s datent de la même année (%s)." % (maj(afx), afy, borne(ax))
    return "%d an%s séparent %s (%s) et %s (%s)." % (ecart, "s" if ecart > 1 else "",
                                                     maj(afx), borne(ax), afy, borne(ay))


# DURÉE d'un événement borné = année de FIN − année de DÉBUT (familles appariées annee_debut_*/annee_fin_*).
# « combien de temps a duré la guerre de Cent Ans ? » -> 116 ans (1337 → 1453). FAUX=0 : deux dates vérifiées
# soustraites (sinon None) ; les deux années sont montrées (re-vérifiables).
_DUREE_FAMILLES = ("guerre", "regne", "dynastie", "bataille", "siege", "revolution", "operation_militaire")
_DUREE_RE = re.compile(
    r"^\s*(?:combien\s+de\s+temps\s+(?:a|ont|a[- ]t[- ](?:il|elle|on))\s+dur[ée]+\s+"
    r"|pendant\s+combien\s+d['’]?\s*(?:ann[ée]+es|temps)\s+.*?dur[ée]+\s+"
    r"|quelle?\s+(?:est|[ée]tait|fut)\s+la\s+dur[ée]e\s+d[eu'’]\s*)"
    r"(.+?)\s*\??\s*$", re.I)


# type-word de tête à retirer pour retrouver la clé PERSONNE (« règne de Louis XIV » -> « Louis XIV » : les
# relations de règne sont clées par le souverain, pas par « règne de … »).
_DUREE_TYPE_TETE_RE = re.compile(
    r"^(?:r[èe]gne|dynastie|mandat|pontificat|principat)\s+(?:du\s+|des\s+|de\s+|d['’]\s*)", re.I)


def _duree_de(entite: str):
    """(début:int, fin:int, affiché, famille) d'un événement borné, ou None. Essaie l'entité TELLE QUELLE puis
    une version sans type-word de tête (« règne de Louis XIV » -> « Louis XIV »). La 1re famille où un candidat a
    À LA FOIS un début ET une fin gagne (FAUX=0 : jamais une durée à moitié inventée)."""
    candidats = [entite]
    sans_type = _DUREE_TYPE_TETE_RE.sub("", entite).strip()
    if sans_type and sans_type != entite:
        candidats.append(sans_type)
    for cand in candidats:
        ne = _normalise(cand)
        for fam in _DUREE_FAMILLES:
            cd = _charge_direct("annee_debut_" + fam).get(ne)
            cf = _charge_direct("annee_fin_" + fam).get(ne)
            if cd and cf:
                d, f = _nombre(cd[1]), _nombre(cf[1])
                if d is not None and f is not None:
                    return int(d), int(f), cd[0], fam
    return None


def _cap_duree(texte: str):
    """DURÉE EXACTE d'un événement borné : « combien de temps a duré la guerre de Cent Ans ? » -> « 116 ans
    (de 1337 à 1453) ». Soustrait deux dates VÉRIFIÉES d'une famille appariée. FAUX=0 : None si l'une des deux
    dates manque ; montre les deux bornes. Gère les dates av. J.-C. (années négatives) et la durée nulle."""
    m = _DUREE_RE.match(texte.strip())
    if not m:
        return None
    ent = _strip_article(m.group(1).strip())
    if not ent or len(ent) < 3:
        return None
    trouve = _duree_de(ent)
    if not trouve:
        return None
    d, f, aff, fam = trouve
    if f < d:                                            # données incohérentes -> on s'abstient plutôt qu'un négatif
        return None
    # sujet correct : le règne/mandat est clé par la PERSONNE -> on remet « Le règne de … » ; sinon l'entité
    # contient déjà son type (« la guerre de … », « la bataille de … ») -> article via realisation_fr.
    prefixe = {"regne": "Le règne de ", "dynastie": "La dynastie ", "mandat": "Le mandat de "}.get(fam)
    if prefixe:
        sujet = prefixe + aff
    else:
        try:
            import realisation_fr as _RF
            sujet = _RF.le_syntagme(aff, majuscule=True)
        except Exception:
            sujet = aff[:1].upper() + aff[1:]
        if _fem_evt(aff) and sujet.startswith("Le "):     # « LA Première Guerre mondiale », pas « Le »
            sujet = "La " + sujet[3:]
    borne = lambda a: ("%d av. J.-C." % -a) if a < 0 else "%d" % a
    n = f - d
    if n == 0:
        return "%s a eu lieu en %s (moins d'un an dans mes données)." % (sujet, borne(d))
    return "%s a duré %d an%s (de %s à %s)." % (sujet, n, "s" if n > 1 else "", borne(d), borne(f))


# ÂGE AU DÉCÈS = année de décès − année de naissance (fait immuable, deux dates stockées). « à quel âge est
# mort Napoléon ? » -> « 51 ans (1769 → 1821) ». Streaming ciblé (fichiers 150 Mo) -> RAM plate. FAUX=0 : None
# si l'une des deux dates manque ; les deux années montrées.
_AGE_RE = re.compile(
    r"^\s*(?:[àa]\s+quel\s+[âa]ge\s+(?:est|s['’]?est|a[- ]t[- ]il|a[- ]t[- ]elle)?\s*"
    r"(?:mort|morte|d[ée]c[ée]d[ée]e?|disparu|disparue|p[ée]ri)\s+"
    r"|quel\s+[âa]ge\s+avait\s+.*?\s+[àa]\s+sa\s+mort\s+)"
    r"(.+?)\s*\??\s*$", re.I)


def _cap_age(texte: str):
    """ÂGE AU DÉCÈS EXACT : « à quel âge est mort Napoléon Ier ? » -> « 51 ans (de 1769 à 1821) ». Soustrait
    l'année de naissance de l'année de décès (deux faits vérifiés). FAUX=0 : None si l'une manque ; av. J.-C. géré."""
    m = _AGE_RE.match(texte.strip())
    if not m:
        return None
    ent = _strip_article(m.group(1).strip())
    if not ent or len(ent) < 3:
        return None
    vn = _lookup_valeur("annee_naissance_personne", ent)
    vd = _lookup_valeur("annee_deces_personne", ent)
    n, d = _nombre(vn) if vn else None, _nombre(vd) if vd else None
    if n is None or d is None:
        return None
    n, d = int(n), int(d)
    if d < n:                                            # données incohérentes -> abstention
        return None
    borne = lambda a: ("%d av. J.-C." % -a) if a < 0 else "%d" % a
    age = d - n
    sujet = ent[:1].upper() + ent[1:]
    return "%s avait %d ans à sa mort (de %s à %s)." % (sujet, age, borne(n), borne(d))


_AGREGAT_RE = re.compile(
    r"(?:quelle?\s+est\s+(?:la\s+|le\s+)?)?(population|superficie|pib)\s+"
    r"(totale?|cumul[ée]+e?s?|moyenne|globale|mediane)\s+"
    r"(?:de\s+l['’ ]?|du\s|des\s|de\s|d['’]|d\s|en\s)\s*"
    r"(?:pays\s+(?:de\s+l['’ ]?|d['’]|d\s|du\s|des\s|de\s|en\s)\s*)?([\wà-ÿ'’\- ]+?)\s*\??\s*$", re.I)
_AGREGAT_ADJ = {"population": "peuple", "superficie": "vaste", "pib": "riche"}


def _cap_agregat(texte: str):
    """AGRÉGATION EXACTE sur un ensemble énuméré : « population totale de l'Afrique ? » -> somme des populations de
    TOUS les pays d'Afrique ; « population moyenne des pays d'Europe » -> moyenne. Un calcul qu'aucun humain ne fait
    de tête et qu'un LLM approxime ; ici c'est exact. FAUX=0 : agrège des faits réels et dit sur combien il agrège."""
    m = _AGREGAT_RE.search(_normalise(texte))
    if not m:
        return None
    attr_mot, op_raw, zone = m.group(1), _normalise(m.group(2)), m.group(3).strip()
    adj = _AGREGAT_ADJ.get(attr_mot)
    if not adj:
        return None
    paires, attr_rel = _membres_attribut("pays", _strip_article(zone), adj)
    if not paires or len(paires) < 2:
        return None
    vals = [v for _e, v in paires]
    unite = _ATTR_UNITE.get(attr_rel, "")
    moyenne = op_raw.startswith("moyen")
    mediane = op_raw.startswith("median")
    if mediane:
        s = sorted(vals)
        val = s[len(s) // 2] if len(s) % 2 else (s[len(s) // 2 - 1] + s[len(s) // 2]) / 2
        libelle, mot_op = "médiane", "médiane sur"
    elif moyenne:
        val, libelle, mot_op = sum(vals) / len(vals), "moyenne", "moyenne sur"
    else:
        val, libelle, mot_op = sum(vals), "totale", "somme de"
    txt = format(int(round(val)), ",d").replace(",", " ")
    try:
        import realisation_fr as _RF
        de_zone = _RF.de(zone.strip()[:1].upper() + zone.strip()[1:], continent=True)
    except Exception:
        de_zone = "de " + zone
    return "La %s %s %s : %s %s (%s %d pays)." % (attr_mot, libelle, de_zone, txt, unite, mot_op, len(paires))


_COMPAR_RE = re.compile(
    r"^\s*(?:est[- ]ce\s+que\s+)?(.+?)\s+est[- ](?:elle|il)\s+(plus|moins|aussi)\s+(\w+)\s+que\s+(.+?)\s*\??\s*$", re.I)
_COMPAR2_RE = re.compile(
    r"(?:qui|quel|quelle|lequel|laquelle)\s+est\s+(?:le\s+|la\s+)?(plus|moins)\s+(\w+)\s+"
    r"(?:entre|de|parmi)\s+(.+?)\s+(?:et|ou)\s+(.+?)\s*\??\s*$", re.I)
_ADJ_PETIT = frozenset("petit petite petits petites court courte courts courtes bas basse leger legere "
                       "legers legeres faible faibles pauvre pauvres".split())
_ATTR_UNITE = {"superficie_pays": "km²", "superficie": "km²", "population_pays": "habitants", "pib_pays": "$",
               "pib_par_habitant_pays": "$/habitant", "altitude": "m", "hauteur": "m", "longueur": "km"}
# unité par PRÉFIXE de relation (familles au-delà des pays) — repli quand la relation exacte n'est pas listée.
_UNITE_PREFIXE = (("altitude", "m"), ("hauteur", "m"), ("longueur", "m"),
                  ("superficie", "km²"), ("population", "habitants"), ("pib", "$"), ("debit", "m³/s"))


def _de_ville(nom: str) -> str:
    """« de <ville> » : les villes n'ont PAS d'article (« de Rome », « d'Athènes ») — sauf celles dont le nom
    l'inclut (« Le Caire » -> « du Caire », « La Havane » -> « de La Havane », « Les Ulis » -> « des Ulis »)."""
    bas = nom.lower()
    if bas.startswith("le "):
        return "du " + nom[3:]
    if bas.startswith("la "):
        return "de " + nom
    if bas.startswith("les "):
        return "des " + nom[4:]
    if bas.startswith(("l'", "l’")):
        return "de " + nom
    if bas[:1] in "aeiouyàâéèêëîïôöùûh":
        return "d'" + nom
    return "de " + nom


def _ville_avec_article(texte: str, ent: str) -> str:
    """Inverse de `_de_ville` : la CONTRACTION porte l'article du nom de ville (« population DU Caire » = de +
    LE Caire ; la donnée est stockée « Le Caire », l'article inclus). Rend la forme candidate à essayer si le
    lookup nu échoue (« Caire » -> None mais « Le Caire » -> trouvé) — vécu 2026-07-06 : « population du Caire »
    servait le nombre BRUT car le cap ratait et la cascade floue prenait le relais. '' si pas de contraction."""
    t = _normalise(texte)
    en = re.escape(_normalise(ent))
    # contraction (du/des) OU article explicite collé à l'entité (« de le Caire » d'une reformulation, « a le
    # Caire »…). L'article doit précéder DIRECTEMENT l'entité -> « la POPULATION de Nice » ne matche pas.
    m = re.search(r"\b(du|des|de\s+la|de\s+l['’]|de\s+le|de\s+les|le|la|les|l['’])\s*" + en + r"\b", t)
    if not m:
        return ""
    a = " ".join(m.group(1).split())
    if a in ("du", "de le", "le"):
        return "Le " + ent
    if a in ("des", "de les", "les"):
        return "Les " + ent
    if a in ("de la", "la"):
        return "La " + ent
    return "L'" + ent                                    # de l' / l'


def _unite_attr(attr_rel: str) -> str:
    """Unité d'affichage d'un attribut : table exacte puis repli par préfixe de famille (« altitude_montagne » -> m)."""
    if attr_rel in _ATTR_UNITE:
        return _ATTR_UNITE[attr_rel]
    for pref, u in _UNITE_PREFIXE:
        if attr_rel.startswith(pref):
            return u
    return ""


def _valeur_attr(entite: str, attr_rel: str):
    """Valeur NUMÉRIQUE d'un attribut pour une entité (lecture directe, insensible aux accents), ou None."""
    cell = _charge_direct(attr_rel).get(_normalise(entite))
    return (_nombre(cell[1]), cell[0]) if cell else (None, None)


def _attr_pour_paire(adjn: str, x: str, y: str):
    """Choisit, dans la famille d'attributs de l'adjectif, la relation qui contient RÉELLEMENT les DEUX entités,
    et renvoie (attr_rel, vx, ax, vy, ay). Généralise au-delà des pays (sommets/altitude, fleuves/longueur) : la
    bonne relation dépend du TYPE des entités, pas d'un choix figé. None si aucune relation n'a les deux."""
    for rel in _ADJ_ATTR.get(adjn, ()):
        vx, ax = _valeur_attr(x, rel)
        if vx is None:
            continue
        vy, ay = _valeur_attr(y, rel)
        if vy is None:
            continue
        return rel, vx, ax, vy, ay
    return None


# ÉCART CHIFFRÉ entre deux entités sur un attribut : « quelle est la différence de population entre X et Y ? ».
# Réutilise le mapping nom->adjectif de l'agrégat et la lecture d'attribut de la comparaison. FAUX=0 : soustrait
# DEUX faits vérifiés (sinon None), montre les deux valeurs et l'écart signé + le rapport.
_DIFF_RE = re.compile(
    r"(?:quelle?\s+est\s+(?:la\s+|le\s+)?)?(?:difference|ecart|distance)\s+d[eu'’]\s*"
    r"(population|superficie|pib)\s+(?:entre|de)\s+(.+?)\s+(?:et|avec)\s+(.+?)\s*\??\s*$", re.I)


# SOMME / MOYENNE sur une LISTE EXPLICITE : « quelle est la population cumulée de la France et de l'Allemagne ? ».
# Additionne (ou moyenne) l'attribut sur des entités NOMMÉES — complète _cap_agregat (sur une zone). FAUX=0 : ne
# somme que des valeurs vérifiées ; signale les entités sans donnée ; dit sur combien il agrège.
_AGREGAT_LISTE_RE = re.compile(
    r"(?:quelle?\s+est\s+(?:la\s+|le\s+)?)?(population|superficie|pib)\s+"
    r"(cumul[ée]+e?|totale?|combin[ée]+e?|additionn[ée]+e?|moyenne)\s+"
    r"(?:du\s+|des\s+|d['’]\s*|de\s+|entre\s+)(.+?)\s*\??\s*$", re.I)


def _cap_agregat_liste(texte: str):
    """SOMME (ou MOYENNE) d'un attribut sur une LISTE EXPLICITE : « population cumulée de la France et de
    l'Allemagne » -> 152 211 586 habitants. FAUX=0 : n'agrège que des valeurs vérifiées ; entités sans donnée
    exclues et signalées ; None si < 2 résolvent (sinon c'est un simple lookup)."""
    m = _AGREGAT_LISTE_RE.search(texte.strip())          # BRUT : garde virgules ET apostrophes (le split en dépend)
    if not m:
        return None
    attr_mot, op_mot, liste = _normalise(m.group(1)), _normalise(m.group(2)), m.group(3)
    # une seule entité « de la France » -> pas une liste (lookup simple) : on exige un séparateur « et/,/ou »
    if not re.search(r"\bet\b|,|\bou\b", liste, re.I):
        return None
    adj = _AGREGAT_ADJ.get(attr_mot)
    attr_rel = next((r for r in _ADJ_ATTR.get(adj, ()) if _charge_direct(r)), None) if adj else None
    if not attr_rel:
        return None
    ents = [_strip_article(e.strip()) for e in re.split(r"\s*,\s*|\s+et\s+|\s+ou\s+", liste, flags=re.I) if e.strip()]
    ents = [e for e in ents if e and len(e) >= 2]
    vals = [(e,) + _valeur_attr(e, attr_rel) for e in ents]
    ok = [(e, v, a) for (e, v, a) in vals if v is not None]
    if len(ok) < 2:
        return None
    moyenne = op_mot.startswith("moyen")
    total = sum(v for (_e, v, _a) in ok)
    res = total / len(ok) if moyenne else total
    unite = _ATTR_UNITE.get(attr_rel, "")
    fmt = lambda v: format(int(round(v)), ",d").replace(",", " ")
    noms = ", ".join(a for (_e, _v, a) in ok)
    manquants = len(ents) - len(ok)
    note = "" if manquants == 0 else " (%d sans donnée, exclu%s)" % (manquants, "s" if manquants > 1 else "")
    if moyenne:
        return "%s moyenne de %s : %s %s%s." % (attr_mot.capitalize(), noms, fmt(res), unite, note)
    return "%s cumulée de %s : %s %s (somme de %d)%s." % (attr_mot.capitalize(), noms, fmt(res), unite, len(ok), note)


# DIMENSION d'une entité précise : « quelle est la hauteur de la tour Eiffel ? », « la longueur du Nil ? ». Cherche
# la valeur via _lookup_direct (repli streaming, famille de relations dont la tête = la dimension) + l'UNITÉ. Léger
# (avant le moteur lourd). FAUX=0 : valeur réelle unique dans la famille, ou None.
_DIMENSION_UNITE = {"hauteur": "m", "altitude": "m", "longueur": "m", "profondeur": "m", "superficie": "km²",
                    "diametre": "m", "largeur": "m", "envergure": "m", "poids": "kg", "masse": "kg"}
_DIMENSION_RE = re.compile(
    r"^\s*(?:quelle?\s+est\s+(?:la\s+|le\s+|l['’])?|quel\s+est\s+(?:le\s+|l['’])?)?"
    r"(hauteur|altitude|longueur|profondeur|superficie|diam[èe]tre|largeur|envergure|poids|masse)\s+"
    r"(?:de\s+la\s+|de\s+l['’]|du\s+|des\s+|de\s+|d['’])(.+?)\s*\??\s*$", re.I)


# SYNONYMES DE TÊTES DE RELATION (compréhension ouverte) : un mot de sens PROCHE d'une relation connue -> la
# relation EXACTE à interroger (pas la famille : « pib » est ambigu entre pib_pays et pib_par_habitant). Carte
# CURÉE et fermée (FAUX=0 : le fait vérifié tranche ; un mauvais routage ne trouve simplement rien). Chaque clé
# NORMALISÉE -> tuple de relations essayées dans l'ordre. Le label d'affichage = le mot de l'utilisateur.
_SYN_TETE = {
    "richesse": ("pib_pays",), "pib": ("pib_pays",),
    "population": ("population_pays", "population_ville"), "superficie": ("superficie", "superficie_pays"),
    "taille": ("superficie",), "etendue": ("superficie",), "aire": ("superficie",), "surface": ("superficie",),
}
# synonymes MULTI-MOTS repliés en un seul token AVANT le parse (« nombre d'habitants » contient un « d' » qui
# casserait le découpage « tête de entité »). Appliqué sur le texte normalisé.
_SYN_TETE_PHRASES = (
    (re.compile(r"\bnombre\s+d['’]?\s*habitants?\b", re.I), "population"),
    (re.compile(r"\bnombre\s+d['’]?\s*ames\b", re.I), "population"),
    (re.compile(r"\bproduit\s+interieur\s+brut\b", re.I), "pib"),
)
# NB : le texte est NORMALISÉ avant ce match (apostrophes -> espaces), donc l'article élidé « l' » devient « l »
# suivi d'un espace : le motif d'article accepte « l['’]\s* » ET « l\s+ ».
_SYN_TETE_RE = re.compile(
    r"^\s*(?:quel(?:le)?\s+(?:est|sont)\s+)?(?:la\s+|le\s+|les\s+|l['’]\s*|l\s+)?"
    r"([\wà-ÿ'’ ]+?)\s+(?:de\s+la|de\s+l['’ ]|du|des|de|d['’ ])\s*(?:la\s+|le\s+|les\s+|l['’]\s*|l\s+)?(.+?)\s*\??\s*$",
    re.I)


def _cap_synonyme_tete(texte: str):
    """SYNONYME DE TÊTE : « la richesse du Japon » -> pib_pays, « la taille de la France » -> superficie, « le
    nombre d'habitants du Japon » -> population. Route un mot de sens proche vers la relation EXACTE et sert la
    valeur vérifiée + unité. FAUX=0 : si l'entité n'est pas dans la relation (« taille de Napoléon » -> pas dans
    superficie), rien n'est renvoyé (None) et le pipeline continue. Léger (lookup streaming, sans moteur lourd)."""
    prepare = _normalise(texte)
    for rx, canon in _SYN_TETE_PHRASES:              # replie les synonymes multi-mots -> un token unique
        prepare = rx.sub(canon, prepare)
    m = _SYN_TETE_RE.match(prepare.strip())
    if not m:
        return None
    mot, ent = m.group(1).strip(), _strip_article(m.group(2).strip(" ?.!\"'«»"))
    rels = _SYN_TETE.get(mot)
    if not rels or not ent or len(ent) < 2 or len(ent.split()) > 5:
        return None
    ville_art = _ville_avec_article(texte, ent)          # « du Caire » -> « Le Caire » (article DANS le nom)
    for rel in rels:
        cell = _lookup_cell(rel, ent) or (_lookup_cell(rel, ville_art) if ville_art else None)
        if cell and cell[1] not in (None, ""):
            n = _nombre(cell[1])
            unite = _unite_attr(rel)
            if _charge_direct("pays_ville").get(_normalise(cell[0])):
                de_ent = _de_ville(cell[0])          # VILLE : « de Rome », « d'Athènes » (pas « du Rome »)
            else:
                try:                                 # français soigné : « du Japon », « de la France »
                    import realisation_fr as _RF
                    de_ent = _RF.de_syntagme(cell[0])
                except Exception:
                    de_ent = "de %s" % cell[0]
            tete_aff = m.group(1).strip().capitalize()
            if n is not None:
                aff = format(int(round(n)), ",d").replace(",", " ") if float(n).is_integer() else "%g" % n
                return "%s %s : %s%s." % (tete_aff, de_ent, aff, (" " + unite) if unite else "")
            return "%s %s : %s." % (tete_aff, de_ent, cell[1])
    return None


# MESURE AMBIGUË (« taille/grandeur/dimension de X ») — COMPOSITEUR du tronc (§10, Phase 2). Vécu 2026-07-07 :
# « la taille de la France » était collapsée EN SILENCE sur superficie (_SYN_TETE) sans signaler que « taille »
# peut vouloir dire population ; « la taille de la tour Eiffel » échouait alors que la hauteur est en base.
_MESURE_AMBIGUE_RE = re.compile(
    r"^\s*(?:quelle?\s+est\s+)?(?:la\s+|le\s+|l['’]\s*)?(taille|grandeur|dimensions?)\s+"
    r"(de\s+la\s+|de\s+l['’]|du\s+|des\s+|de\s+|d['’])\s*(.+?)\s*\??\s*$", re.I)


def _cap_mesure_ambigue(texte: str):
    """Tête de mesure AMBIGUË -> le faisceau tient TOUTES les lectures en parallèle (G2 : jamais un sens choisi
    en silence) : chaque lecture est résolue par les caps VÉRIFIÉS existants (_cap_dimension pour hauteur/
    longueur — avec ses gardes anti-homonymes d'œuvres —, _cap_synonyme_tete pour superficie/population), puis
    `tronc.compose` sert le coup calculé (§10.1 : le certain + les lectures + l'invitation). FAUX=0 : seule une
    branche au format « Relation de X : valeur. » (lookup réel) devient un fait servi ; les messages d'abstention
    des caps ne sont JAMAIS pris pour des branches. None hors périmètre -> cascade inchangée."""
    m = _MESURE_AMBIGUE_RE.match(texte.strip())
    if not m:
        return None
    try:
        import tronc as _T
    except Exception:
        return None
    tete = _normalise(m.group(1))
    lectures = _T.RELATIONS_AMBIGUES.get("dimension" if tete.startswith("dimension") else tete)
    de, ent = m.group(2), m.group(3).strip(" ?.!\"'«»")
    if not lectures or not ent or len(ent.split()) > 6:
        return None
    # GARDE HOMONYME : un PAYS/une VILLE n'a pas de « hauteur » — sans cette garde, « taille de la France »
    # servait « Hauteur de France : 232 m » (le PAQUEBOT France, homonyme — FAUX réel vécu 2026-07-07).
    if _charge_direct("capitale").get(_normalise(ent)) or _charge_direct("pays_ville").get(_normalise(ent)):
        lectures = tuple(r for r in lectures if r not in ("hauteur", "longueur"))
    cands = []
    for rel in lectures:
        q2 = "%s %s%s" % (rel, de, ent)                       # « hauteur de la tour Eiffel » (article gardé)
        r = _cap_dimension(q2) if rel in ("hauteur", "longueur") else _cap_synonyme_tete(q2)
        # une BRANCHE n'est un fait que si le cap a servi un lookup (« X de Y : valeur. »), jamais une abstention
        ok = bool(r) and " : " in r and not r.startswith(("Je ", "Plusieurs "))
        cands.append(_T.Candidat(intention=_T.INTERROGER_FAIT, entites=(ent,), relation=rel,
                                 statut=_T.TRANCHE if ok else _T.NON_TRANCHE, reponse=r if ok else "",
                                 ancrage="lookup vérifié (lecteur)" if ok else "non ancré",
                                 signal_discriminant=rel, confiance=0.9 if ok else 0.0,
                                 provenance="compositeur mesure ambiguë (%s)" % rel))
    return _T.compose(_T.Faisceau(tuple(cands)), terme=m.group(1).strip().lower())


def _cap_dimension(texte: str):
    """DIMENSION d'une entité : « quelle est la hauteur de la tour Eiffel ? » -> valeur + unité. Cherche dans la
    FAMILLE de relations de la dimension (hauteur_tour, hauteur_barrage…) via _lookup_direct (streaming). FAUX=0 :
    valeur réelle unique, ou None (entité absente / ambiguë). Léger : répond sans charger le moteur lourd."""
    m = _DIMENSION_RE.match(texte.strip())
    if not m:
        return None
    dim, ent = _normalise(m.group(1)), _strip_article(m.group(2).strip())
    if not ent or len(ent) < 2 or len(ent.split()) > 6:
        return None
    if _est_concept_commun(ent):                         # « longueur du bonheur » : nom commun -> pas une entité mesurable
        return None
    # dimensions SŒURS (« hauteur du mont Everest » : la donnée vit dans altitude_montagne). Le TYPE-WORD de
    # l'entité (« MONT Everest ») DÉSAMBIGUÏSE : il désigne la relation typée (altitude_MONTAGNE) là où le nom
    # nu est ambigu (« Everest » est aussi une localité à 350 m). Piste « ne jamais figer l'atome » : l'entité
    # apparente cache (type + nom) — on exploite les deux au lieu de jeter le type.
    dims = (dim,) + {"hauteur": ("altitude",), "altitude": ("hauteur",)}.get(dim, ())
    type_rels, nu = (), None
    for pref, types in (("mont ", ("montagne", "sommet")), ("montagne ", ("montagne",)),
                        ("pic ", ("pic", "sommet", "montagne")), ("mont-", ("montagne", "sommet")),
                        ("lac ", ("lac",)), ("île ", ("ile",)), ("ile ", ("ile",))):
        if ent.lower().startswith(pref) and len(ent) > len(pref) + 1:
            type_rels, nu = types, ent[len(pref):]
            break
    val = None
    for d in dims:
        if nu:                                           # typé : la relation du TYPE d'abord (précise, non ambiguë)
            for rel in _relations():
                if rel.split("_")[0] == d and any(t in rel for t in type_rels):
                    cell = _lookup_cell(rel, ent) or _lookup_cell(rel, nu)   # « mont Blanc » ENTIER d'abord
                    if cell and cell[1] not in (None, ""):
                        val = cell[1]
                        break
        if val is None or str(val).strip() == "":
            fam = _lookup_famille(d, ent)                # forme complète, VALEURS de toute la famille
            if nu:                                       # entité GÉO typée (« mont/lac/île X ») : jamais servie
                fam = [c for c in fam if not any(          # par un TABLEAU homonyme (« Mont Blanc », 0,559 m !)
                    tk in _RELS_OEUVRE_ART or tk in ("sculpture", "statue") for tk in c[0].split("_")[1:])]
            uniq = {str(c[2]) for c in fam}
            if len(uniq) == 1:
                val = fam[0][2]
            elif len(uniq) > 1:
                # HOMONYMES à valeurs DIFFÉRENTES (« La Joconde » : 2,48 m ET 0,534 m — deux œuvres distinctes,
                # aucune n'étant forcément celle demandée) : on le DIT — sinon la cascade lourde en pioche une
                # au hasard (FAUX réel trouvé cette nuit sur « hauteur de la tour Eiffel » -> tableau 0,632 m).
                vs = " ; ".join(sorted(uniq)[:4])
                return ("Plusieurs « %s » homonymes ont des valeurs de %s DIFFÉRENTES dans mes données (%s) — "
                        "je ne devine pas lequel tu veux, précise (« le tableau X », « le monument X »)."
                        % (ent, dim, vs))
        if val is not None and str(val).strip():
            break
    if val is None or str(val).strip() == "":
        if _est_monument(ent):
            # MONUMENT connu sans dimension stockée : couper court ICI — la cascade lourde servirait la
            # dimension d'une ŒUVRE D'ART homonyme (« La Tour Eiffel », tableau de 0,632 m, pour le monument !)
            return ("Je connais bien %s (monument), mais je n'ai pas sa %s vérifiée dans mes données — et je ne "
                    "confonds pas avec les œuvres d'art homonymes qui en ont une. Je m'abstiens." % (ent, dim))
        if _est_tableau_connu(ent) and dim in ("hauteur", "largeur", "longueur", "taille"):
            # PEINTURE connue sans dimension picturale stockée : même court-circuit (la sculpture homonyme
            # « La Joconde » de 2,48 m n'est pas le tableau de Vinci)
            return ("Je connais bien %s (tableau), mais ses dimensions ne sont pas dans mes données — et je ne "
                    "confonds pas avec une sculpture homonyme. Je m'abstiens." % ent)
        return None
    n = _nombre(val)
    unite = _DIMENSION_UNITE.get(dim, "")
    de_ent = ("du %s" % ent) if ent.lower().startswith(("mont ", "pic ", "lac ")) else ("de %s" % ent)
    if n is not None and unite:
        aff = format(int(n), ",d").replace(",", " ") if float(n).is_integer() else "%g" % n
        # LISIBILITÉ : une longueur stockée en mètres ≥ 10 km s'affiche d'abord en km (« 6 300 km ») — la
        # valeur brute reste montrée (re-vérifiable). Conversion exacte /1000, aucun arrondi caché.
        if unite == "m" and float(n) >= 10000 and (float(n) / 1000).is_integer():
            return "%s %s : %s km (%s m)." % (dim.capitalize(), de_ent,
                                              format(int(n // 1000), ",d").replace(",", " "), aff)
        return "%s %s : %s %s." % (dim.capitalize(), de_ent, aff, unite)
    return "%s %s : %s." % (dim.capitalize(), de_ent, val)


# MÊME ATTRIBUT ? « la France et l'Allemagne sont-elles sur le même continent ? » -> compare la valeur d'un attribut
# pour DEUX entités. Rare cas où « Non » est SÛR (deux faits vérifiés comparés). FAUX=0 : None si l'un manque.
_MEME_MOT_REL = {"continent": "continent", "pays": "pays_ville", "monnaie": "monnaie", "capitale": "capitale",
                 "langue": "langue_officielle", "president": "president_pays", "region": "region_pays"}
_MEME_RE = re.compile(
    r"^\s*(?:est[- ]ce\s+que\s+)?(.+?)\s+et\s+(.+?)\s+(?:sont|ont|est|se\s+trouvent)[- ]?(?:ils|elles|il|elle)?\s+"
    r"(?:sur\s+|dans\s+|dans\s+l['’]|de\s+|d['’])?(?:le\s+|la\s+|les\s+|l['’]|un\s+|une\s+)?"
    r"m[êe]mes?\s+(continent|pays|monnaie|capitale|langue|president|region)\b.*$", re.I)


def _cap_meme_attribut(texte: str):
    """« X et Y ont-ils le/la même ATTR ? » (continent, pays, monnaie, capitale, langue…) -> compare les valeurs
    vérifiées des deux entités. FAUX=0 : « Oui » si égales, « Non » (avec les deux valeurs) si différentes — le
    « Non » est SOUND car les DEUX faits sont vérifiés ; None si l'un manque (abstention honnête)."""
    m = _MEME_RE.match(texte.strip())
    if not m:
        return None
    x, y, mot = _strip_article(m.group(1).strip()), _strip_article(m.group(2).strip()), _normalise(m.group(3))
    rel = _MEME_MOT_REL.get(mot) or _MEME_MOT_REL.get(mot.rstrip("s"))
    if not rel:
        return None
    # Valeur VÉRIFIÉE par le chemin ROBUSTE (famille de relations via le moteur), PAS un lookup direct sur un
    # seul .jsonl : la relation exacte peut être incomplète (ex. `monnaie.jsonl` sans les pays de la zone euro,
    # que le moteur connaît par ailleurs). Sinon « France et Allemagne, même monnaie ? » abstenait à tort.
    def _valeur(ent):
        cell = _lookup_cell(rel, ent)
        if cell and cell[1] not in (None, ""):
            return cell[0], str(cell[1])
        ia, _ = _charge_ia()
        if ia:
            vf = _val_par_famille(ia, mot, ent) or _lookup_direct(mot, ent)
            if vf not in (None, ""):
                return ent, str(vf)
        return None
    rx, ry = _valeur(x), _valeur(y)
    if not rx or not ry:
        return None
    nx, vx = rx
    ny, vy = ry
    fem = mot in ("monnaie", "capitale", "langue", "region")     # accord « la même » / « le même »
    meme = "la même" if fem else "le même"
    if _normalise(vx) == _normalise(vy):
        return "Oui — %s et %s ont %s %s : %s." % (nx, ny, meme, mot, vx)
    return "Non — %s a pour %s %s, tandis que %s a %s." % (nx, mot, vx, ny, vy)


def _cap_difference(texte: str):
    """ÉCART EXACT entre deux entités sur un attribut chiffré : « quelle est la différence de population entre la
    France et l'Allemagne ? » -> la valeur absolue de l'écart, les deux populations et le rapport. FAUX=0 : deux
    faits vérifiés soustraits (sinon None) ; l'ordre est rétabli (« X compte N de plus que Y »)."""
    m = _DIFF_RE.search(_normalise(texte))
    if not m:
        return None
    attr_mot, x, y = m.group(1), m.group(2), m.group(3)
    adj = _AGREGAT_ADJ.get(attr_mot)
    attr_rel = next((r for r in _ADJ_ATTR.get(adj, ()) if _charge_direct(r)), None) if adj else None
    if not attr_rel:
        return None
    vx, ax = _valeur_attr(_strip_article(x.strip()), attr_rel)
    vy, ay = _valeur_attr(_strip_article(y.strip()), attr_rel)
    if vx is None or vy is None:
        return None
    unite = _ATTR_UNITE.get(attr_rel, "")
    ecart = abs(vx - vy)
    fmt = lambda v: (format(int(v), ",d").replace(",", " ") if float(v).is_integer() else "%g" % v)
    try:
        import realisation_fr as _RF
        nx, ny = _RF.article_pays(ax), _RF.article_pays(ay)
    except Exception:
        nx, ny = ax, ay
    if ecart == 0:
        return "%s et %s sont à égalité : %s %s." % (nx, ny, fmt(vx), unite)
    haut, bas = (nx, ny) if vx > vy else (ny, nx)
    rapport = max(vx, vy) / min(vx, vy) if min(vx, vy) else 0
    txt_rapport = (", soit %.1f× plus" % rapport) if rapport >= 1.15 else ""
    return ("%s a %s %s de plus que %s (%s vs %s%s)."
            % (haut, fmt(ecart), unite, bas, fmt(max(vx, vy)), fmt(min(vx, vy)), txt_rapport))


# COMPARAISON N-ENTITÉS : « qui est le plus peuplé entre la France, l'Allemagne et l'Italie ? ». ARGMAX borné sur
# une LISTE explicite (≥3 entités) — le 2-entités reste géré par _cap_comparaison. FAUX=0 : compare des valeurs
# vérifiées, montre la valeur gagnante et le nombre comparé ; abstention si < 2 entités résolvent.
_COMPARN_RE = re.compile(
    # préfixe interrogatif OPTIONNEL (« le plus peuplé entre la France, l'Allemagne et l'Italie ? » court)
    r"^\s*(?:(?:qui|quel|quelle|lequel|laquelle)\s+est\s+)?(?:le\s+|la\s+)?(plus|moins)\s+(\w+)\s+"
    r"(?:entre|parmi)\s+(.+?)\s*\??\s*$", re.I)


def _cap_comparaison_nway(texte: str):
    """ARGMAX sur une LISTE explicite d'entités (« le plus peuplé entre la France, l'Allemagne et l'Italie »).
    FAUX=0 : compare des valeurs vérifiées ; None si < 2 entités résolvent. Choisit la relation de la famille où
    le PLUS d'entités ont une valeur (généralise pays/sommets/fleuves via _ADJ_ATTR)."""
    m = _COMPARN_RE.match(texte.strip())
    if not m:
        return None
    direction, adj_aff, liste = m.group(1), m.group(2).lower(), m.group(3)
    adj = _normalise(adj_aff)
    ents = [_strip_article(e.strip()) for e in re.split(r"\s*,\s*|\s+et\s+|\s+ou\s+", liste) if e.strip()]
    ents = [e for e in ents if e and len(e) >= 2]
    if len(ents) < 3:                                # 2 entités -> laissé à _cap_comparaison (message dédié)
        return None
    familles = _ADJ_ATTR.get(adj, ())
    if not familles:
        return None
    # relation de la famille où le MAXIMUM d'entités résolvent (ensemble comparable le plus large)
    best_rel, best_vals = None, []
    for rel in familles:
        if not _charge_direct(rel):
            continue
        vals = [(e,) + _valeur_attr(e, rel) for e in ents]
        ok = [(e, v, a) for (e, v, a) in vals if v is not None]
        if len(ok) > len(best_vals):
            best_rel, best_vals = rel, ok
    if not best_rel or len(best_vals) < 2:
        return None
    maximise = (direction == "plus") != (adj in _ADJ_PETIT)
    gagnant = (max if maximise else min)(best_vals, key=lambda t: t[1])
    unite = _unite_attr(best_rel)
    fmt = lambda v: (format(int(v), ",d").replace(",", " ") if float(v).is_integer() else "%g" % v)
    pays = best_rel.endswith("_pays") or best_rel in ("superficie", "pib_pays")
    try:
        import realisation_fr as _RF
        nom = _RF.article_pays(gagnant[2]) if pays else _RF.le_syntagme(gagnant[2])
    except Exception:
        nom = gagnant[2]
    manquants = len(ents) - len(best_vals)
    note = "" if manquants == 0 else " (%d sans donnée, exclu%s)" % (manquants, "s" if manquants > 1 else "")
    return "%s — le %s %s des %d comparés : %s %s%s." % (
        nom[:1].upper() + nom[1:], direction, adj_aff, len(best_vals), fmt(gagnant[1]), unite, note)


def _cap_comparaison(texte: str):
    """COMPARAISON EXACTE de deux entités sur un attribut (« la France est-elle plus grande que l'Espagne ? »,
    « qui est le plus peuplé entre l'Inde et la Chine ? »). Compare DEUX faits vérifiés et montre les valeurs.
    FAUX=0 : jamais de confirmation sans les deux faits ; on énonce le vrai ordre si l'assertion est fausse."""
    # GRANDEURS À UNITÉS d'abord (« 100 km/h est-il plus rapide que 30 m/s ? ») : conversion exacte puis
    # comparaison (fonction_nl.compare_grandeurs) — sinon ces questions mouraient en repli honnête (vécu).
    try:
        import fonction_nl as _FNL
        _cg = _FNL.compare_grandeurs(texte)
    except Exception:
        _cg = None
    if _cg:
        return _cg
    x = y = adj = direction = None
    m = _COMPAR_RE.match(texte)
    if m:
        x, direction, adj, y = m.group(1), m.group(2), m.group(3), m.group(4)
    else:
        m = _COMPAR2_RE.search(texte)
        if not m:
            return None
        direction, adj, x, y = m.group(1), m.group(2), m.group(3), m.group(4)
    adjn = _normalise(adj)
    x, y = _strip_article(x.strip()), _strip_article(y.strip())
    # FEUILLE SUPERLATIVE d'un côté de la comparaison : « le pays le plus peuplé d'Europe est-il plus peuplé
    # que le Japon ? » -> résout d'abord l'argmax borné (fait réel), compare ensuite. La résolution est MONTRÉE.
    notes = []
    if re.search(r"\b(?:le|la)\s+plus\b|\b(?:le|la)\s+moins\b", x, re.I):
        arg = _superlatif_argmax(x)
        if arg:
            notes.append(arg[1])
            x = _strip_article(str(arg[0]))
    if re.search(r"\b(?:le|la)\s+plus\b|\b(?:le|la)\s+moins\b", y, re.I):
        arg = _superlatif_argmax(y)
        if arg:
            notes.append(arg[1])
            y = _strip_article(str(arg[0]))
    suffixe_notes = ("  (en résolvant d'abord : %s)" % " ; ".join(notes)) if notes else ""
    trouve = _attr_pour_paire(adjn, x, y)            # relation où les DEUX entités ont une valeur (pays OU sommets/fleuves)
    if not trouve:
        return None
    attr_rel, vx, ax, vy, ay = trouve
    unite = _unite_attr(attr_rel)
    fx = "%s %s" % (format(int(vx), ",d").replace(",", " "), unite) if float(vx).is_integer() else "%g %s" % (vx, unite)
    fy = "%s %s" % (format(int(vy), ",d").replace(",", " "), unite) if float(vy).is_integer() else "%g %s" % (vy, unite)
    pays = attr_rel.endswith("_pays") or attr_rel in ("superficie", "pib_pays")   # famille « pays » -> article_pays
    try:
        import realisation_fr as _RF
        if pays:
            nx, ny = _RF.article_pays(ax), _RF.article_pays(ay)  # « la France », « l'Espagne », « l'Inde »
        else:
            nx, ny = _RF.le_syntagme(ax), _RF.le_syntagme(ay)    # « le mont Blanc », « la Loire », « l'Everest »
    except Exception:
        nx, ny = ax, ay
    if direction == "aussi" or vx == vy:
        return "%s (%s) et %s (%s) sont %ségaux sur ce critère.%s" % (nx, fx, ny, fy,
                                                                      "quasi " if vx != vy else "", suffixe_notes)
    grand_sens = adjn not in _ADJ_PETIT          # « grand/peuplé » : valeur haute = « plus » ; « petit » : inverse
    if direction == "moins":
        grand_sens = not grand_sens
    passe = (vx > vy) == grand_sens
    if passe:
        return "Oui — %s (%s) est %s %s que %s (%s).%s" % (nx, fx, direction, adj, ny, fy, suffixe_notes)
    return "Non — c'est l'inverse : %s (%s) est %s %s que %s (%s).%s" % (ny, fy, direction, adj, nx, fx, suffixe_notes)


_FILTRE_RE = re.compile(
    # ordre IMPORTANT : les formes LONGUES (proportion/pourcentage) avant « quels? » — sinon « quel » de « quel
    # pourcentage » matche « quels? » et le type devient « pourcentage ».
    r"(?:quelle\s+proportion\s+(?:de\s+l['’ ]?|des\s+|du\s+)|quel\s+pourcentage\s+(?:de\s+l['’ ]?|des\s+|du\s+)|"
    r"combien\s+de|quels?)\s*([a-zà-ÿ]+)\s+"
    r"(?:de\s+l['’ ]?|du\s|des\s|de\s|d['’]|d\s|en\s)\s*([\wà-ÿ'’\- ]+?)\s+"
    r"(?:ont|a|avec|comptent|possedent|abritent)\b[^0-9]*?"
    r"(plus|moins|superieur\w*|inferieur\w*|au\s+moins|au\s+plus)\s+(?:de\s+|a\s+)?"
    r"(\d[\d\s.,]*)\s*(milliard\w*|million\w*|millier\w*|mille)?", re.I)
# INTERVALLE : « quels pays d'Afrique ont entre 10 et 50 millions d'habitants ? » — les DEUX bornes, inclusives.
# La magnitude peut être partagée (« entre 10 et 50 millions » -> 10e6..50e6) ou propre à chaque borne
# (« entre 500 000 et 2 millions »). Même familles de verbes que le filtre à seuil.
_FILTRE_ENTRE_RE = re.compile(
    r"(?:quels?|combien\s+de)\s+([a-zà-ÿ]+)\s+(?:de\s+l['’ ]?|du\s|des\s|de\s|d['’]|d\s|en\s)\s*([\wà-ÿ'’\- ]+?)\s+"
    r"(?:ont|a|avec|comptent|possedent|abritent)\b[^0-9]*?"
    r"entre\s+(\d[\d\s.,]*)\s*(milliard\w*|million\w*|millier\w*|mille)?\s*et\s+"
    r"(\d[\d\s.,]*)\s*(milliard\w*|million\w*|millier\w*|mille)?", re.I)
_MAGNITUDE = {"mille": 1e3, "millier": 1e3, "milliers": 1e3, "million": 1e6, "millions": 1e6,
              "milliard": 1e9, "milliards": 1e9}


def _nombre_seuil(brut: str, magn) -> float:
    """« 1,5 » + « millions » -> 1_500_000.0 (ValueError si illisible). `brut` vient du texte NORMALISÉ, où la
    virgule décimale a pu devenir une ESPACE (« 1,5 » -> « 1 5 ») : un dernier groupe de 1-2 chiffres après espace
    est relu comme décimales ; les groupes de 3 restent des séparateurs de milliers (« 1 500 000 »)."""
    s = re.sub(r"[^\d\s.,]", "", brut).replace(",", ".").strip()
    parts = s.split()
    if len(parts) > 1 and "." not in s and len(parts[-1]) < 3:
        s = "".join(parts[:-1]) + "." + parts[-1]
    else:
        s = "".join(parts)
    return float(s) * _MAGNITUDE.get(magn, 1.0)


def _cap_filtre(texte: str):
    """FILTRAGE MULTI-CRITÈRES EXACT : « quels pays d'Afrique ont plus de 100 millions d'habitants ? » (seuil) ou
    « … ont entre 10 et 50 millions d'habitants ? » (intervalle, bornes incluses) -> la machine parcourt
    EXHAUSTIVEMENT l'ensemble énuméré et ne garde que ceux qui passent. Un LLM énumère de mémoire (et se trompe) ;
    ici c'est exact et complet. FAUX=0 : entités réelles filtrées sur un attribut vérifié."""
    qn = _normalise(texte)
    lo = hi = None
    m = _FILTRE_ENTRE_RE.search(qn)
    if m:
        typ_raw, zone, n1, mg1, n2, mg2 = m.groups()
        try:
            lo, hi = _nombre_seuil(n1, mg1), _nombre_seuil(n2, mg2)
            # « entre 10 et 50 millions » : la magnitude porte sur les DEUX bornes — mais SEULEMENT si la 1re
            # borne est un petit nombre nu (≤ 3 chiffres) ET que la lecture héritée reste croissante.
            # « entre 500 000 et 2 millions » (nombre complet) garde sa valeur littérale.
            if mg1 is None and mg2 and len(re.sub(r"\D", "", n1)) <= 3:
                lo_herite = _nombre_seuil(n1, mg2)
                if lo_herite <= hi:
                    lo = lo_herite
        except ValueError:
            return None
        if lo > hi:
            lo, hi = hi, lo                        # bornes données à l'envers -> on lit l'intervalle voulu
    else:
        m = _FILTRE_RE.search(qn)
        if not m:
            return None
        typ_raw, zone, direction, nombre, magn = m.groups()
    typ = typ_raw[:-1] if (typ_raw.endswith(("s", "x")) and len(typ_raw) > 4) else typ_raw
    if typ not in _APPARTENANCE:
        return None
    if re.search(r"superficie|km2|km²|\bkm\b|vaste|grand|etendu", qn):
        adj, unite = "vaste", "km²"
    else:
        adj, unite = "peuple", "habitants"
    fmt = lambda v: format(int(v), ",d").replace(",", " ")
    if lo is not None:                             # INTERVALLE (bornes incluses, lecture naturelle de « entre »)
        garde = lambda v: lo <= v <= hi
        sens, seuil_txt = "entre", "%s et %s" % (fmt(lo), fmt(hi))
    else:                                          # SEUIL (comportement historique inchangé)
        try:
            seuil = _nombre_seuil(nombre, magn)
        except ValueError:
            return None
        au_dessus = direction.startswith(("plus", "superieur", "au moins"))
        limite_incluse = direction in ("au moins", "au plus")
        def garde(v):
            if au_dessus:
                return v >= seuil if limite_incluse else v > seuil
            return v <= seuil if limite_incluse else v < seuil
        sens, seuil_txt = ("plus de" if au_dessus else "moins de"), fmt(seuil)
    paires, _ = _membres_attribut(typ, _strip_article(zone), adj)
    if not paires:
        return None
    sel = [(e, v) for e, v in paires if garde(v)]        # paires déjà triées desc
    pluriel = typ if typ.endswith(("s", "x")) else typ + "s"
    zone_aff = zone.strip()[:1].upper() + zone.strip()[1:]
    # PROPORTION / POURCENTAGE : « quelle proportion des pays d'Afrique ont plus de 50 M d'habitants ? » -> N/total
    # + pourcentage. Exact (ensemble énuméré). FAUX=0 : ratio de faits réels.
    if re.match(r"^\s*(?:quelle\s+proportion|quel\s+pourcentage)\b", qn):
        pct = 100.0 * len(sel) / len(paires)
        return "%d des %d %s %s ont %s %s %s, soit %.0f %%." % (len(sel), len(paires), pluriel, _RF_de(zone_aff),
                                                               sens, seuil_txt, unite, pct)
    # COMPTAGE CONDITIONNEL : « combien de pays d'Afrique ont plus de 50 millions d'habitants ? » -> le NOMBRE
    # (pas la liste). Exact car l'ensemble est énuméré. FAUX=0 : compte des entités réelles qui passent le seuil.
    if re.match(r"^\s*combien\b", qn):
        return "%d %s %s ont %s %s %s (compté exactement)." % (len(sel), pluriel, _RF_de(zone_aff), sens,
                                                               seuil_txt, unite)
    if not sel:
        return "Aucun %s %s n'a %s %s %s (d'après mes données)." % (typ, _RF_de(zone_aff), sens, seuil_txt, unite)
    cap = 20
    lignes = ["· %s (%s %s)" % (e, fmt(v), unite) for e, v in sel[:cap]]
    reste = "\n… (%d autres)" % (len(sel) - cap) if len(sel) > cap else ""
    entete = "%d %s %s ont %s %s %s :" % (len(sel), pluriel, _RF_de(zone_aff), sens, seuil_txt, unite)
    return entete + "\n" + "\n".join(lignes) + reste


def _RF_de(zone: str) -> str:
    """« d'Afrique »/« de France »… pour un en-tête de filtre (élision/genre via realisation_fr, repli élision simple)."""
    try:
        import realisation_fr as _RF
        return _RF.de(zone, continent=True)
    except Exception:
        return "d'" + zone if re.match(r"[aeiouyàâäéèêëîïôöùûü]", _normalise(zone)) else "de " + zone


_NB_MOTS = {"un": 1, "une": 1, "deux": 2, "trois": 3, "quatre": 4, "cinq": 5, "six": 6, "sept": 7,
            "huit": 8, "neuf": 9, "dix": 10, "douze": 12, "quinze": 15, "vingt": 20}
_CLASST_RE = re.compile(
    r"(?:les|quels?\s+sont\s+les|donne(?:[- ]moi)?\s+les|cite(?:[- ]moi)?\s+les|top)\s+"
    r"(?:(\d+|un|une|deux|trois|quatre|cinq|six|sept|huit|neuf|dix|douze|quinze|vingt)\s+)?"
    r"(?:des\s+|meilleurs?\s+)?"
    r"(?:(?!plus\b|moins\b)(\w+)\s+)?(?:les\s+|la\s+|le\s+)?(?:plus|moins)\s+(\w+)"
    r"(?:\s+(\w+))?\s+(?:de\s+l['’]?|du\s|des\s|de\s|d['’]|d\s|en\s)\s*(.+?)\s*\??\s*$", re.I)


# CLASSEMENT d'une LISTE EXPLICITE : « classe la France, l'Allemagne et l'Italie par population ». Tri complet
# (pas seulement le gagnant) d'entités nommées sur un attribut. FAUX=0 : valeurs vérifiées, exclut les inconnues.
_CLASST_LISTE_RE = re.compile(
    r"^\s*(?:classe|classer|range|ranger|ordonne|ordonner|trie|trier)\s+"
    r"(?:ces\s+\w+\s*:?\s*|les\s+\w+\s*:?\s*)?(.+?)\s+"
    r"(?:par|selon|d['’]apr[èe]s|en\s+fonction\s+de(?:\s+la|\s+leur)?)\s+"
    r"(population|superficie|pib|habitants?|taille|altitude|richesse)\s*(croissante?|d[ée]croissante?)?\s*\??\s*$",
    re.I)
# forme ALTERNATIVE : « range ces pays par superficie : France, Espagne, Portugal » (liste APRÈS l'attribut).
_CLASST_LISTE2_RE = re.compile(
    r"^\s*(?:classe|classer|range|ranger|ordonne|ordonner|trie|trier)\s+(?:ces\s+\w+\s+|les\s+\w+\s+)?"
    r"(?:par|selon|d['’]apr[èe]s|en\s+fonction\s+de(?:\s+la|\s+leur)?)\s+"
    r"(population|superficie|pib|habitants?|taille|altitude|richesse)\s*(croissante?|d[ée]croissante?)?\s*:\s*"
    r"(.+?)\s*\??\s*$", re.I)
_CLASST_MOT_ADJ = {"population": "peuple", "habitant": "peuple", "habitants": "peuple", "superficie": "vaste",
                   "taille": "vaste", "pib": "riche", "richesse": "riche", "altitude": "haut"}


def _cap_classement_liste(texte: str):
    """TRI COMPLET d'une LISTE EXPLICITE sur un attribut : « classe la France, l'Allemagne et l'Italie par
    population » -> l'ordre décroissant (croissant si demandé) avec les valeurs. FAUX=0 : valeurs vérifiées ;
    entités inconnues exclues et signalées ; None si < 2 résolvent."""
    m = _CLASST_LISTE_RE.match(texte.strip())
    if m:
        liste, attr_mot, sens_mot = m.group(1), _normalise(m.group(2)), _normalise(m.group(3) or "")
    else:
        m = _CLASST_LISTE2_RE.match(texte.strip())     # forme « par ATTR : liste »
        if not m:
            return None
        attr_mot, sens_mot, liste = _normalise(m.group(1)), _normalise(m.group(2) or ""), m.group(3)
    adj = _CLASST_MOT_ADJ.get(attr_mot) or _CLASST_MOT_ADJ.get(attr_mot.rstrip("s"))
    if not adj:
        return None
    ents = [_strip_article(e.strip()) for e in re.split(r"\s*,\s*|\s+et\s+|\s+ou\s+", liste) if e.strip()]
    ents = [e for e in ents if e and len(e) >= 2]
    if len(ents) < 2:
        return None
    best_rel, best = None, []
    for rel in _ADJ_ATTR.get(adj, ()):
        if not _charge_direct(rel):
            continue
        ok = [(e, v, a) for e in ents for (v, a) in [_valeur_attr(e, rel)] if v is not None]
        if len(ok) > len(best):
            best_rel, best = rel, ok
    if not best_rel or len(best) < 2:
        return None
    croissant = sens_mot.startswith("croiss")
    best.sort(key=lambda t: t[1], reverse=not croissant)
    unite = _unite_attr(best_rel)
    fmt = lambda v: (format(int(v), ",d").replace(",", " ") if float(v).is_integer() else "%g" % v)
    lignes = ["%d. %s (%s %s)" % (i + 1, a, fmt(v), unite) for i, (e, v, a) in enumerate(best)]
    manquants = len(ents) - len(best)
    note = "" if manquants == 0 else "\n(%d sans donnée, exclu%s)" % (manquants, "s" if manquants > 1 else "")
    ordre = "croissant" if croissant else "décroissant"
    return "Classement par %s (%s) :\n%s%s" % (attr_mot, ordre, "\n".join(lignes), note)


# RANG d'une entité dans son ensemble : « quel est le rang de la France par population en Europe ? » -> position
# dans le classement. Reuse _membres_attribut (ensemble énuméré, complet). FAUX=0 : rang EXACT ou None.
_RANG_MOT_ADJ = {"population": "peuple", "habitants": "peuple", "superficie": "vaste", "taille": "vaste",
                 "pib": "riche", "richesse": "riche"}
_RANG_RE = re.compile(
    r"^\s*(?:quel\s+est\s+le\s+rang|[àa]\s+quelle\s+place|quelle\s+place\s+occupe|en\s+quelle\s+position)\s+"
    r"(?:de\s+la\s+|de\s+l['’]|du\s+|des\s+|de\s+|d['’]|est\s+(?:la\s+|le\s+|l['’])?)?(.+?)\s+"
    r"(?:par|selon|en\s+termes?\s+de|pour\s+la|au\s+niveau\s+de\s+la)\s+"
    r"(population|superficie|taille|pib|richesse|habitants)\s+"
    r"(?:en\s+|dans\s+l['’]?|d['’]|du\s+|des\s+|de\s+l['’]?|de\s+)(.+?)\s*\??\s*$", re.I)


def _cap_rang(texte: str):
    """RANG d'une entité dans son ensemble : « quel est le rang de la France par population en Europe ? » -> « 4ᵉ
    sur 47 ». Position EXACTE dans le classement d'un ensemble énuméré. FAUX=0 : sur un ensemble complet le rang est
    certain ; None si l'entité n'est pas dans l'ensemble. Gardé aux types sûrs (pays)."""
    m = _RANG_RE.match(texte.strip())
    if not m:
        return None
    ent, attr_mot, zone = _strip_article(m.group(1).strip()), _normalise(m.group(2)), _strip_article(m.group(3).strip())
    adj = _RANG_MOT_ADJ.get(attr_mot) or _RANG_MOT_ADJ.get(attr_mot.rstrip("s"))
    if not adj:
        return None
    paires, _ = _membres_attribut("pays", zone, adj)         # ensemble énuméré (trié desc)
    if not paires or len(paires) < 2:
        return None
    ne = _normalise(ent)
    rang = next((i + 1 for i, (e, _v) in enumerate(paires) if _normalise(e) == ne), None)
    if rang is None:
        return None
    val = next(v for e, v in paires if _normalise(e) == ne)
    aff = next(e for e, v in paires if _normalise(e) == ne)
    ord_txt = "1er" if rang == 1 else "%dᵉ" % rang
    unite = _ATTR_UNITE.get(next((r for r in _ADJ_ATTR.get(adj, ()) if _charge_direct(r)), ""), "")
    vf = format(int(val), ",d").replace(",", " ") if float(val).is_integer() else "%g" % val
    try:
        import realisation_fr as _RF
        sujet = _RF.article_pays(aff, majuscule=True)        # « La France », « L'Allemagne »
    except Exception:
        sujet = aff
    ens = "au monde" if _normalise(zone) in _ZONES_GLOBALES else _RF_de(zone.capitalize())
    return "%s est %s sur %d pays %s par %s (%s %s)." % (sujet, ord_txt, len(paires), ens, attr_mot, vf, unite)


def _cap_classement(texte: str):
    """CLASSEMENT / TOP-N : « les 5 pays les plus peuplés d'Afrique » -> tri EXACT + valeurs. La machine ORDONNE des
    faits réels ; un LLM devine l'ordre. FAUX=0 : sur un ensemble énuméré, l'ordre est certain."""
    m = _CLASST_RE.search(texte)
    if not m:
        return None
    nb_tok, typ1, adj, typ2, zone = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5).strip()
    n = 5 if not nb_tok else (int(nb_tok) if nb_tok.isdigit() else _NB_MOTS.get(_normalise(nb_tok), 5))
    typ = next((t for t in (_normalise(typ1 or ""), _normalise(typ2 or "")) if t in _APPARTENANCE), None)
    adjn = _normalise(adj)
    if adjn not in _ADJ_ATTR and _normalise(typ2 or "") in _ADJ_ATTR:
        adjn = _normalise(typ2)
    if not typ or adjn not in _ADJ_ATTR:
        return None
    # TRI : « plus » -> valeurs hautes, « moins » -> basses ; INVERSÉ si l'adjectif est « petit » (« les 3 plus
    # PETITS pays » = superficies MINIMALES). Le MOT d'affichage garde l'original (« plus petits »), indépendant.
    sens_mot = "moins" if "moins" in _normalise(texte).split() else "plus"
    maximise = (sens_mot == "plus") != (adjn in _ADJ_PETIT)
    paires, _ = _membres_attribut(typ, _strip_article(zone), adjn)
    if not paires or len(paires) < 2:
        return None
    classe = paires if maximise else list(reversed(paires))
    n = max(1, min(n, len(classe)))
    lignes = ["%d. %s (%s)" % (i + 1, e, ("%d" % v if float(v).is_integer() else "%g" % v))
              for i, (e, v) in enumerate(classe[:n])]
    sens = sens_mot
    pluriel = typ if typ.endswith(("s", "x")) else typ + "s"
    de = "d'" + zone if re.match(r"[aeiouyhàâäéèêëîïôöùûü]", _normalise(zone)) else "de " + zone
    return "Les %d %s les %s %s %s :\n%s" % (n, pluriel, sens, adj, de, "\n".join(lignes))


_COMPTE_RE = re.compile(
    r"\bcombien\s+(?:y\s+a[- ]?t[- ]?il\s+|existe[- ]?t[- ]?il\s+|il\s+y\s+a\s+)?(?:de\s+|d['’])([\wà-ÿ'’\- ]+?)"
    r"(?:\s+(?:y\s+a[- ]?t[- ]?il|existe[- ]?t[- ]?il|il\s+y\s+a|connais[- ]?tu|as[- ]?tu))?"
    r"(?:\s+(?:en|dans|de\s+l['’]?|du|des|de|d['’]|compte\s+(?:la\s+|le\s+|l['’])?|comporte\s+(?:la\s+|le\s+|l['’])?|"
    r"contient\s+(?:la\s+|le\s+|l['’])?)\s*([\wà-ÿ'’\- ]+?))?\s*\??\s*$", re.I)


def _cap_comptage(texte: str):
    """COMPTAGE EXACT : « combien de pays en Afrique ? » -> 54 (compté, pas deviné) ; « combien de félins ? » ->
    nombre d'hyponymes réels. C'est LE point fort machine vs LLM (les LLM comptent mal). FAUX=0 : compte des entités
    RÉELLES d'un ensemble énuméré ; abstention si l'ensemble n'est pas identifiable."""
    m = _COMPTE_RE.search(texte)
    if not m:
        return None
    typ = _strip_article((m.group(1) or "").strip())
    zone = _strip_article((m.group(2) or "").strip()) if m.group(2) else None
    if not typ or len(typ) < 3:
        return None
    typn = _normalise(typ)
    sing = typn[:-1] if (typn.endswith(("s", "x")) and len(typn) > 4) else typn
    # GARDE DURÉE COMPOSÉE (vécu 2026-07-08) : « 2 semaines et 3 jours ça fait combien de jours » comptait
    # les 10 hyponymes du concept « jour » — c'est une composition de durées (fonction_nl), pas un comptage.
    if sing in ("jour", "heure", "minute", "seconde", "semaine", "moi", "mois", "an", "annee") \
            and re.search(r"\d\s*(?:ans?|annees?|mois|semaines?|jours?|heures?|minutes?|h\b)", _normalise(texte)):
        return None                                      # (h\b compact : « de 9h à 17h30 » = durée, vécu)
    # GARDE LETTRES (FAUX vécu 2026-07-08) : « le mot X contient combien de consonnes » comptait les 37
    # hyponymes du concept « consonne » — c'est un comptage de LETTRES dans un mot, traité par _cap_texte.
    if sing in ("voyelle", "consonne", "lettre", "syllabe", "mot", "caractere") and re.search(
            r"\bmot\b|\bdans\b", _normalise(texte)):
        return None
    # MONDE ENTIER : « combien de pays dans le monde ? » -> somme des pays rattachés à un continent (ensemble
    # complet — même base que le superlatif mondial). HONNÊTE : le décompte « officiel » dépend de la définition
    # (193 membres ONU) -> on dit ce qu'on compte.
    if sing == "pays" and (not zone or _normalise(zone) in ("monde", "le monde", "terre", "la terre", "planete")):
        par_cont = _charge_reverse("continent")
        if par_cont:
            tous = set()
            for _cn, (_aff, ents) in par_cont.items():
                tous.update(_normalise(e) for e in ents)
            if tous:
                return ("%d pays rattachés à un continent dans mes données (compté exactement — le décompte "
                        "« officiel » dépend de la définition : l'ONU reconnaît 193 États membres)." % len(tous))
    if zone:                                     # membres d'un type dans une zone (pays en Afrique…)
        for rel_app in _APPARTENANCE.get(sing, _APPARTENANCE.get(typn, ())):
            hit = _charge_reverse(rel_app).get(_normalise(zone))
            if hit and hit[1]:
                # FAUX=0 : « compté exactement » n'est vrai que pour un ensemble COMPLET (pays). Pour les types à
                # membership troué (montagnes/villes), on cadre en RECALL (« je connais N … ») — on ne prétend PAS
                # au total exhaustif (il y a bien plus de montagnes en Europe que celles que la base référence).
                typ_pl = typ if typ.endswith(("s", "x")) else typ + "s"      # accord au pluriel (201 montagnes)
                if sing in _SUPERLAT_TYPES_SÛRS:
                    return "%d %s en %s (compté exactement dans mes données)." % (len(hit[1]), typ_pl, zone)
                return "Je connais %d %s en %s dans mes données (liste non exhaustive)." % (len(hit[1]), typ_pl, zone)
        return None
    # CONTINENTS : le compte est une CONVENTION (5 à 7 selon les modèles) — le graphe is-a rangerait aussi
    # paléo/super-continents. Réponse curée honnête plutôt que « 27 termes classés continent ».
    if sing == "continent" and not zone:
        return ("7 selon le modèle courant (Afrique, Amérique du Nord, Amérique du Sud, Antarctique, Asie, "
                "Europe, Océanie) — mais c'est une CONVENTION : d'autres modèles en comptent 5 ou 6 "
                "(Amériques réunies, Eurasie).")
    try:                                         # sans zone : nombre d'hyponymes réels (« combien de félins »)
        import est_un as _E
        hy = _E.hyponymes(sing, limite=100000)
    except Exception:
        hy = []
    if len(hy) >= 3:
        # RECALL de classification, PAS le compte canonique : le graphe is-a peut ranger sous « continent » des
        # sur/paléocontinents et des termes rares. On le DIT honnêtement (« termes … que je classe comme »).
        return "Je connais %d termes que je classe comme « %s » dans mes données." % (len(hy), sing)
    return None


def _superlatif_argmax(expr: str):
    """FEUILLE SUPERLATIVE par ARGMAX BORNÉ : « le pays le plus peuplé d'Afrique » -> Nigeria, en comparant TOUS les
    membres énumérés (les pays d'Afrique) sur un attribut vérifié (population). SOUND tant que l'ensemble est complet :
    on ne devine pas, on COMPARE des faits réels et on peut montrer le décompte. Renvoie (entité, étape) ou None."""
    nz = _normalise(expr)
    toks = nz.split()
    if "plus" not in toks and "moins" not in toks:
        return None
    # LEFT (le SN superlatif) de ZONE
    m = re.search(r"^(.*?)\s+(?:de la|de l|du|des|de|d)\s+(.+)$", nz)
    if not m:
        return None
    gauche, zone = m.group(1).strip(), m.group(2).strip()
    gtoks = [w for w in gauche.split() if w not in ("le", "la", "les", "l", "plus", "moins", "un", "une")]
    # adjectif = 1er token juste après plus/moins ; type = un token connu d'appartenance
    idx = next((i for i, w in enumerate(gauche.split()) if w in ("plus", "moins")), -1)
    apres = gauche.split()[idx + 1:] if idx >= 0 else []
    adj = next((w for w in apres if w in _ADJ_ATTR), None) or next((w for w in gtoks if w in _ADJ_ATTR), None)
    typ = next((w for w in gtoks if w in _APPARTENANCE), None)
    if not adj or not typ:
        return None
    # sens : « plus » maximise, « moins » minimise ; INVERSÉ si l'adjectif est lui-même « petit » (« le plus
    # PETIT pays » = superficie MINIMALE). Sans ça, « le plus petit pays » renvoyait le plus GRAND.
    maximise = ("moins" not in toks) != (adj in _ADJ_PETIT)
    # FAUX=0 : un superlatif AFFIRME « le plus X » — ce n'est SAIN que si l'ensemble énuméré est COMPLET. Les pays
    # d'un continent le sont (membership « continent » exhaustif). PAS les montagnes/villes : continent_montagne
    # oublie l'Elbrouz (vrai plus haut d'Europe) et le Mont Blanc n'a pas d'altitude -> l'argmax dirait « Cervin »
    # (faux). Pour ces types on S'ABSTIENT plutôt que d'affirmer un extrême sur un ensemble troué.
    if typ not in _SUPERLAT_TYPES_SÛRS:
        return None
    attr_rel = next((r for r in _ADJ_ATTR[adj] if _charge_direct(r)), None)
    if not attr_rel:
        return None
    attr = _charge_direct(attr_rel)
    # membres = entités du type dont l'appartenance == zone (reverse-lookup). ZONE GLOBALE (« du monde ») : TOUS
    # les membres du type = toutes les entités ayant l'attribut (ensemble pays complet -> superlatif SOUND).
    if _normalise(zone) in _ZONES_GLOBALES:
        membres = [c[0] for c in attr.values()]
    else:
        membres = None
        for rel_app in _APPARTENANCE[typ]:
            rev = _charge_reverse(rel_app)
            hit = rev.get(zone) or next((v for k, v in rev.items() if k == zone), None)
            if hit and hit[1]:
                membres = hit[1]
                break
        if not membres:
            return None
    best = None
    n_compares = 0
    for ent in membres:
        cell = attr.get(_normalise(ent))
        if not cell:
            continue
        x = _nombre(cell[1])
        if x is None:
            continue
        n_compares += 1
        if best is None or (x > best[1] if maximise else x < best[1]):
            best = (cell[0], x)
    if not best or n_compares < 2:
        return None
    sens = "plus" if maximise else "moins"
    return best[0], "%s = %s (%s %s sur %d %s comparés)" % (expr, best[0], sens, adj, n_compares, typ)


def _dist(a: str, b: str) -> int:
    """Distance d'édition (Levenshtein), bornée : >2 d'écart de longueur -> on abandonne (99)."""
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if abs(la - lb) > 2:
        return 99
    prev = list(range(lb + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[lb]


def _mot_reel(tok: str) -> bool:
    """Le token est-il un VRAI mot français (lemme OU forme fléchie courante) ? Sert à NE PAS proposer de
    « did-you-mean » sur un mot réel (« longue »->« langue », « riche »->« roche », « peint »->« point » =
    faux signaux : ce sont des mots, pas des fautes). Ne FORCE PAS le chargement lourd : si la connaissance
    n'est pas prête (mode léger), on s'abstient (False) -> comportement inchangé hors mode plein."""
    # LEXIQUE POS EMBARQUÉ (~19k mots, sans chargement lourd) : garde universel — « inventer », « créer »,
    # « lister » y sont. Vécu 2026-07-06 : le did-you-mean proposait « inventer »->« inventeur » sur une
    # demande créative, car _est_mot_connu (ci-dessous) ne couvre pas les infinitifs verbaux.
    if _normalise(tok) in _charge_mots_valides():
        return True
    if not pret():
        return False
    try:
        emc = importlib.import_module("resolution")._est_mot_connu
    except Exception:
        return False
    if emc(tok):
        return True
    # Formes fléchies dont le LEMME nu n'est pas ingéré (verbes surtout : « invente »->« inventer »). Test léger.
    variantes = set()
    if tok.endswith("e"):
        variantes |= {tok + "r", tok[:-1] + "er"}        # invente -> inventer
    if tok.endswith("ent"):
        variantes.add(tok[:-3] + "er")                   # inventent -> inventer
    if tok.endswith("ee"):
        variantes.add(tok[:-2] + "er")                   # peuplee -> peupler
    if tok.endswith("s"):
        variantes.add(tok[:-1])
    return any(emc(v) for v in variantes if len(v) >= 4)


def _suggere_type(question: str) -> tuple[str, str] | None:
    """« did-you-mean » AGNOSTIQUE : un mot de la question est-il une quasi-faute d'un mot-type CONNU (n'importe
    quel token de relation, tous domaines) ? « flauve »≈« fleuve », « monnaye »≈« monnaie », etc. Conservateur
    (≥5 lettres, distance ≤1, ≤2 pour les longs). NE propose RIEN sur un VRAI mot français (`_mot_reel`) : sinon
    « longue/riche/peint/chine » seraient « corrigés » à tort. Renvoie (mot_saisi, forme_proposée) ou None."""
    cibles = {t for t in _vocab_types() if len(t) >= 5}
    for tok in set(_normalise(question).split()):
        # _mot_defini en RENFORT de _mot_reel : « espace » manquait au lexique POS mais est DÉFINI dans
        # definition_nom -> le did-you-mean proposait « espece » sur un mot parfaitement français (bug réel).
        if len(tok) < 5 or tok in cibles or _mot_reel(tok) or _mot_defini(tok):
            continue
        meilleure = None
        for cible in cibles:
            if cible[0] != tok[0]:          # MÊME INITIALE exigée : une faute la préserve quasi toujours (cf.
                continue                    # corrige()). Tue « france »->« branche » (token concurrent) tout en
            d = _dist(tok, cible)           # gardant « flauve »->« fleuve », « monnaye »->« monnaie » (dist 1).
            # DISTANCE ≤1 SEULEMENT : la quasi-totalité des vraies fautes sont à 1 édition. La dist-2 attrapait surtout
            # des FAUX POSITIFS = de VRAIS mots ayant un token-relation voisin à 2 éditions (« administrative »≈
            # « administration », « traverse »≈« travees ») -> did-you-mean abusif. dist ≤1 = précision (et _mot_reel
            # ne couvre pas tous les mots réels via le lexique). Aucun cas légitime connu ne dépend de la dist-2.
            seuil = 1
            if d <= seuil and (meilleure is None or d < meilleure[1]):
                meilleure = (cible, d)
        if meilleure:
            prop = meilleure[0]
            # supprime les suggestions TRIVIALES = simple FLEXION (l'un préfixe de l'autre : « ecrit »->« ecrite »,
            # « lettre »->« lettres ») : aucune valeur d'aide, et souvent un faux signal (« qui a écrit » -> « ecrite »).
            if prop.startswith(tok) or tok.startswith(prop):
                continue
            return (tok, prop)
    return None


# Mots qui ne DÉSIGNENT jamais un type d'entité (comparatifs/liaisons) mais figurent dans des NOMS de relations
# (`plus_longue_travee_pont`) : « 100 km/h est-il PLUS rapide que 30 m/s » matchait « plus » -> liste de PONTS
# ancrée sur « 100 » (FAUX vécu 2026-07-08). Fermé, sûr.
_JAMAIS_TYPE = frozenset({"plus", "moins", "tres", "grande", "grand", "longue", "long", "haute", "haut",
                          "petite", "petit"})


def _liste_inverse(question: str) -> str | None:
    """REQUÊTE INVERSE GÉNÉRIQUE « quels <B> en/de <valeur> ? » sur N'IMPORTE quelle relation `A_B` du registre
    (géo, art, sport, chimie…). Aucun domaine codé en dur. Soundness : on liste les VRAIES entités taguées de la
    valeur nommée, sinon None (jamais d'invention). Le mot-type doit matcher un token de nom de relation, ET une
    valeur réelle doit apparaître dans la question (double ancrage = peu de faux positifs)."""
    qn = _normalise(question)
    qtoks = set(qn.split())
    # mots « demandés » = tokens de la question + synonymes (_ALIAS) + variantes singulier/pluriel.
    demandes = set(qtoks)
    for w in qtoks:
        if w in _ALIAS:
            demandes.add(_ALIAS[w])
        if w.endswith(("s", "x")):       # pluriels FR en -s ET en -x (château -> châteaux)
            demandes.add(w[:-1])
        demandes.add(w + "s")
    # GARDE ANTI-FAUX : l'ÉNUMÉRATION inverse n'a de sens que pour une vraie demande de LISTE. On l'autorise si :
    #   (a) intention de liste explicite (« cite/liste/tous… ») ; OU
    #   (b) le type apparaît au PLURIEL (« quels FLEUVES… », « les MUSÉES… ») ; OU
    #   (c) le type est INTERROGÉ directement (« quel FLEUVE traverse… » = quels fleuves).
    # « (quelle est la) composition de l'ÉQUIPE de France » ne remplit AUCUN cas (type singulier, objet de
    # « composition de ») -> on s'abstient (sinon on listerait à tort les 49 équipes de France = FAUX).
    intent = bool(qtoks & _INTENT_LISTE_INV)
    seq = qn.split()

    def _base(w):
        # alias d'abord, puis SINGULARISATION nue : « langues » -> « langue » (sans ça, un pluriel hors-alias
        # ne retombait jamais sur son token de relation -> « quelles langues parle-t-on au Japon » ne listait pas)
        if w in _ALIAS:
            return _ALIAS[w]
        if w.endswith(("s", "x")):
            return _ALIAS.get(w[:-1]) or w[:-1]
        return w

    def _liste_plausible(rel) -> bool:
        rtoks = [t for t in rel.split("_") if len(t) >= 3 and t not in _GENERIQUES and t not in _JAMAIS_TYPE]
        for i, w in enumerate(seq):
            # GARDE INVARIABLE (#90) : un mot en -s/-x précédé d'un DÉTERMINANT SINGULIER (« LE prix », « LA voix »)
            # n'est PAS un pluriel-liste — « prix/voix/croix/nez/temps/cas » sont invariables. Sinon « en quelle année
            # Einstein a gagné LE prix Nobel » (question singulière) listait à tort les 22 lauréats. « LES prix » ou
            # « quels prix » (pluriel/interrogatif réels) déclenchent toujours.
            det_sing = i > 0 and seq[i - 1] in _DET_SINGULIER
            pluriel = (len(w) >= 4 and w.endswith(("s", "x")) and (_base(w) in rtoks or w in rtoks)
                       and not det_sing)
            interroge = (i > 0 and seq[i - 1] in _INTERRO_TYPE and (_base(w) in rtoks or w in rtoks))
            if pluriel or interroge:
                return True
        return False

    # relations candidates : un token de NOM (≥3, non générique) est demandé dans la question (ET liste plausible).
    candidats = []
    for rel in _relations():
        toks_match = [tk for tk in rel.split("_")
                      if len(tk) >= 3 and tk not in _GENERIQUES and tk not in _JAMAIS_TYPE and tk in demandes]
        if toks_match and (intent or _liste_plausible(rel)):
            candidats.append((rel, toks_match))
    for rel, toks_match in candidats:
        par_val = _charge_reverse(rel)
        if not par_val:
            continue
        rtoks = set(rel.split("_"))    # garde anti-coïncidence : la VALEUR ne doit pas être un mot du NOM de la
        #                                relation (« capitale de la LUNE » : « lune » est à la fois le token de
        #                                `plus_grande_lune` ET sa valeur -> on ne liste pas « terre »).
        best = None       # la VALEUR (la plus longue) nommée dans la question -> ancre la requête
        for vn, (disp, ents) in par_val.items():
            # GARDE ANCRE≠TYPE : la valeur d'ancrage ne peut pas être le mot-TYPE interrogé lui-même, ni son
            # alias (« quel FLEUVE traverse Paris » : « fleuve » est une VALEUR de type_riviere ET l'alias du
            # token « riviere » -> sans ce garde, on listait les 147 rivières de type fleuve en ignorant Paris).
            if _base(vn) in rtoks:
                continue
            # GARDE ANCRE CIRCULAIRE (FAUX vécu 2026-07-08) : « de quelle ANNÉE date le roman 1984 » DEMANDE
            # une année — le « 1984 » de la phrase est un TITRE (le roman d'Orwell), pas une ancre de liste ;
            # sans garde, on servait les 2041 édifices construits en 1984. Une ancre NUMÉRIQUE n'est légitime
            # que si le type interrogé est AUTRE que la date elle-même (« quels ÉDIFICES datent de 1984 » OK).
            if vn.isdigit() and set(toks_match) <= {"annee", "annees", "date", "dates"}:
                continue
            if (len(vn) >= 3 and vn not in rtoks and re.search(r"\b" + re.escape(vn) + r"\b", qn)
                    and (best is None or len(vn) > len(best[0]))):
                best = (vn, disp, ents)
        if not best or not best[2]:
            continue
        _, disp, ents = best
        cap = 12
        montre = ", ".join(ents[:cap])
        reste = f" … (échantillon alphabétique ; {len(ents) - cap} autres)" if len(ents) > cap else ""
        label = _LABELS.get(rel) or (next((t for t in reversed(rel.split("_")) if t not in _GENERIQUES), rel)).capitalize()
        cav = _CAVEATS.get(rel)              # caveat = avertissement réel (≠ source) -> conservé ; source masquée
        suffixe = f"  ({cav})" if cav else ""
        return f"{label} ({disp}, {len(ents)}) : {montre}{reste}{suffixe}"
    return None


def _listage(question: str) -> str | None:
    """Délègue au moteur les requêtes de LISTAGE (« pays de l'Europe », « cite un continent »). Import paresseux
    de `resolution` (le lecteur est déjà chargé en mode plein). Renvoie une chaîne formatée ou None."""
    ia, _ = _charge_ia()
    if not ia:
        return None
    try:
        return importlib.import_module("resolution").resout_liste(question)
    except Exception:
        return None


def _fiche(question: str) -> str | None:
    """Étage 1d : SYNTHÈSE d'entité (« parle-moi de la France ») — agrège les faits vérifiés en réponse de longueur
    variable. SOUND (faits réels ou None). Après les lookups précis : ne court-circuite pas une réponse ciblée."""
    ia, _ = _charge_ia()
    if not ia:
        return None
    try:
        return importlib.import_module("resolution").resout_fiche(question)
    except Exception:
        return None


def _raisonnement(question: str) -> str | None:
    """Étage 1a : RAISONNEMENT sur les faits vérifiés (superlatif « la plus haute montagne de France » -> mont
    Blanc, via une relation EXPLICITE et exacte). SOUND : renvoie une vraie réponse ou None (jamais un argmax sur
    base incomplète). Tenté AVANT le lookup pour qu'un superlatif obtienne sa VRAIE réponse plutôt qu'un HORS."""
    ia, _ = _charge_ia()
    if not ia:
        return None
    try:
        R = importlib.import_module("resolution")
        return R.resout_superlatif(question) or R.resout_comparaison(question)
    except Exception:
        return None


# LOCALISATION « où se trouve X ? » / « coordonnées de X ? » -> réponse depuis les coordonnées INGÉRÉES (capitales +
# 378k localités). Le lookup NL générique ne verbalise PAS une paire (lat, lon) comme UNE réponse -> sans ce garde,
# « où se trouve Toulouse » restait HORS alors que la donnée existe. SOUND : `ia.coordonnees_lieu` renvoie des coords
# VÉRIFIÉES ou None (jamais deviné). On n'attrape QUE les formes locationnelles explicites, pas « où en es-tu ».
_LOC_RE = re.compile(r"^(?:ou (?:se (?:trouve|situe)|est(?: situ[ée]e?)?)|"
                     r"(?:quelles?\s+sont\s+les\s+|donne\s+(?:moi\s+)?les\s+|)coordonn[ée]es(?:\s+geographiques)?(?:\s+de| du| des| d)|"
                     r"localise|situe)\s+(.+?)\s*\??\s*$")


def _localisation(question: str) -> str | None:
    """« Où se trouve X ? » / « coordonnées de X ? » -> « X est situé à 43.604°N, 1.443°E. » depuis les coordonnées
    ingérées, ou None (entité inconnue -> HORS honnête, jamais deviné). SOUND : coords vérifiées seulement."""
    m = _LOC_RE.match(_normalise(question))
    if not m:
        return None
    ia, _ = _charge_ia()
    if not ia:
        return None
    lieu = _strip_article(m.group(1))
    if not lieu or _est_concept_commun(lieu):    # « où se trouve le bonheur ? » : concept, pas un toponyme
        return None                              # (hameau « Bonheur » = faux-ami) -> abstention (FAUX=0)
    try:
        c = ia.coordonnees_lieu(lieu)
    except Exception:
        return None
    if not c:
        return None
    lat, lon = c
    ns = "N" if lat >= 0 else "S"
    eo = "E" if lon >= 0 else "O"
    return f"{lieu} est situé à {abs(lat):.3f}°{ns}, {abs(lon):.3f}°{eo} (coordonnées géographiques)."


def pret() -> bool:
    """La connaissance lourde est-elle DÉJÀ chargée ? Permet au serveur de NE PAS bloquer un message le temps du
    chargement (~70 s) : tant que ce n'est pas prêt, on répond depuis la seule mémoire de dialogue (instantané),
    et on passe en connaissance complète dès que le préchauffage de fond a fini."""
    return _IA not in (None, False)


def _connaissance_rapide_daemon(question: str, conv_id: str | None = None) -> str | None:
    """CHEMIN RAPIDE (opt-in, sans régression) : si le daemon résident `lecteur_daemon` tourne, répondre un
    fait EXACT via `lecteur_client` SANS cold-load du moteur lourd (~622 Mo). Le daemon sert EXACTEMENT
    `lecteur.repond_nl` (= le cœur de `ia.donnee_nl`) -> FAUX=0 préservé. Daemon absent -> None (l'appelant
    garde le chemin lourd habituel : aucune régression). Ne gère que l'exact ; les fautes de frappe restent
    au chemin lourd (résolution floue)."""
    try:
        import lecteur_client
        from base_faits import VERIFIE
        if not lecteur_client.disponible():
            return None
        statut, valeur = lecteur_client.repond_nl(question)
    except Exception:
        return None
    if statut == VERIFIE and valeur is not None:
        suj = _sujet_de(question)
        if conv_id and suj:
            _DERNIER_SUJET[conv_id] = suj
            _DERNIER_QUESTION[conv_id] = question
        return str(valeur)                        # identique à `fait.valeur` du chemin lourd
    return None


# Gabarit « [quelle est] la REL de [la] ENTITÉ ? » — la structure factuelle nominale la plus courante. Partagé
# entre le repli-famille de `_connaissance_verifiee` et la brique « structure reconnue mais non ancrée ».
_REL_DE_ENT_RE = re.compile(
    r"^\s*(?:quel(?:le)?s?\s+(?:est|sont)\s+)?(?:la\s+|le\s+|les\s+|l['] ?)?"
    r"([\wà-ÿ]+)\s+(?:de\s+la|de\s+l['] ?|du|des|de)\s+(?:la\s+|le\s+|les\s+|l['] ?)?(.+?)\s*\??\s*$", re.I)


# Valeur numérique NUE + unité déclarée par la SOURCE -> on affiche l'unité (FAUX-adjacent vécu 2026-07-08 :
# « point de fusion du fer » -> « 1811 » nu, lu en °C alors que la vérité stockée est en KELVINS ; « distance
# Terre-Soleil » -> « 150 » nu). Table FERMÉE sur le libellé exact des sources ; jamais d'unité devinée.
_UNITE_SOURCE = (("point de fusion (K)", "K"), ("point d'ébullition (K)", "K"),
                 ("°C/°F→K affine", "K"), ("millions de km", "millions de km"),
                 ("→ kg/m³", "kg/m³"), ("(en mm)", "mm"),
                 ("convertie en mètres", "m"), ("masse atomique standard (u)", "u"))


_DERNIERE_VALEUR: dict = {}                   # conv_id -> (valeur float, unité str) de la dernière réponse à unité


def _avec_unite(fait, conv_id=None) -> str:
    v = str(fait.valeur)
    if not re.fullmatch(r"-?\d+(?:[.,]\d+)?", v.strip()):
        return v
    src = str(getattr(fait, "source", "") or "")
    for marqueur, unite in _UNITE_SOURCE:
        if marqueur in src:
            if conv_id:                       # « et en celsius ? » au tour suivant convertit CETTE valeur
                _DERNIERE_VALEUR[conv_id] = (float(v.replace(",", ".")), unite)
            return f"{v} {unite}"
    return v


def _connaissance_verifiee(question: str, conv_id: str | None = None) -> str | None:
    """Étage 2 : un fait VÉRIFIÉ du borné, ou None. Jamais d'invention (HORS -> None). TOLÈRE une faute de
    frappe sur l'entité via `donnee_nl_floue` (« protugal »->« portugal ») et le SIGNALE honnêtement.
    Effet de bord MULTI-TOURS : si ça répond et qu'un SUJET est extractible, on le mémorise pour `conv_id`."""
    rapide = _connaissance_rapide_daemon(question, conv_id)   # daemon lecteur (opt-in) -> réponse sans cold-load
    if rapide is not None:
        return rapide
    ia, verifie = _charge_ia()
    if not ia:
        return None
    try:
        floue = getattr(ia, "donnee_nl_floue", None)
        if floue is not None:
            statut, fait, correction = floue(question)
        else:                                   # compat : ancien moteur sans résolution floue
            statut, fait = ia.donnee_nl(question)
            correction = None
    except Exception:
        return None
    if fait is not None and statut == verifie:
        suj = correction or _sujet_de(question)   # le sujet retenu = entité corrigée, sinon extraite
        if conv_id and suj:
            _DERNIER_SUJET[conv_id] = suj
            _DERNIER_QUESTION[conv_id] = question  # mémorise la question résolue (pour la continuation type B)
        prefixe = f"(en comprenant « {correction} ») " if correction else ""
        return f"{prefixe}{_avec_unite(fait, conv_id)}"   # source vérifiée en interne, non affichée (préférence
        #                                           Yohan) ; l'UNITÉ déclarée par la source est ajoutée (kelvins…)
    # REPLI FAMILLE : « continent de France » peut ne pas matcher un gabarit direct alors que la relation existe
    # sous un nom de famille (continent_pays…). On parse « rel de entité » et on essaie la famille (unicité exigée,
    # FAUX=0). N'affecte JAMAIS une réponse déjà résolue (on n'arrive ici que si le DATA a rendu HORS).
    mfam = _REL_DE_ENT_RE.match(question)
    if mfam and _normalise(mfam.group(1)) in _attr_heads():
        vf = _val_par_famille(ia, mfam.group(1).strip(), mfam.group(2).strip(" ?.\"'«»"))
        if vf:
            return str(vf)
    # Le DATA n'a rien : tenter un SOUS-SYSTÈME FONCTION (morse/OTAN/masse molaire/complément ADN). Sound : le
    # moteur renvoie VÉRIFIÉ ou HORS (jamais inventé). On exige un mot-clé fort -> aucune question DATA mal routée.
    fc = _fonction_calculee(question)
    if fc is not None and conv_id:
        # CONTINUATION sur un CALCUL (vécu 2026-07-08 : « masse molaire de H2O » puis « et de CO2 ? » tombait
        # en repli — le sujet n'était mémorisé que pour le DATA). Sujet = queue après la DERNIÈRE préposition
        # (l'opérande), COURTE seulement (≤ 3 tokens — une queue verbeuse ferait une substitution absurde).
        msuj = re.search(r"^.*\b(?:de|d['’]|en|à)\s+([\wÀ-ÿ][\w À-ÿ%/.-]*?)\s*\??\s*$", question)
        if msuj and msuj.group(1).strip() and len(msuj.group(1).split()) <= 3:
            _DERNIER_SUJET[conv_id] = msuj.group(1).strip()
            _DERNIER_QUESTION[conv_id] = question
    return fc


def _fonction_calculee(question: str) -> str | None:
    """Étage 2bis : une FONCTION calculée bornée (code morse, alphabet OTAN, masse molaire, complément ADN) ou
    None. Module LÉGER `fonction_nl` (pas de lecteur). FAUX=0 : on ne formate que le verdict VÉRIFIÉ du moteur."""
    try:
        import fonction_nl
        from base_faits import VERIFIE
        statut, texte, source = fonction_nl.resout_fonction(question)
    except Exception:
        return None
    if statut == VERIFIE and texte is not None:
        return texte                              # source vérifiée en interne, non affichée (préférence Yohan)
    return None


# Coordination de plusieurs sous-questions dans UNE demande (« capitale de la France ET numéro du fer »). On NE
# coupe PAS sur un « et » de tête (continuation « et sa monnaie ? ») : le regex exige des espaces des DEUX côtés.
_COORD_RE = re.compile(r"\s+(?:et|puis|ainsi que)\s+|\s*[;,]\s+")


def _resout_partie(p: str):
    """Résout UNE sous-question : données/fonctions (capitale, masse molaire, morse…) OU calcul (mots ET symbolique).
    Renvoie la réponse (str) ou None. FAUX=0 : ne renvoie que des verdicts VÉRIFIÉS, jamais une devinette."""
    r = _connaissance_verifiee(p, None)
    if r:
        return r
    p_math = re.sub(r"(?<=\d)\s*[x×]\s*(?=\d)", "*", p)   # 5x9 / 5 × 9 -> 5*9
    try:
        import fonction_nl
        from base_faits import VERIFIE
        st, val, _ = fonction_nl.resout_arithmetique(p_math)
        if st == VERIFIE and val is not None:
            return str(val)
    except Exception:
        pass
    try:
        import classifieur_bornage as _CB
        v = _CB._juge_arith(_CB._norm(p_math))
        if v is not None:
            return str(int(v) if isinstance(v, float) and v.is_integer() else v)
    except Exception:
        pass
    return None


# INTENTION DE CALCUL explicite : « combien font/fait/valent/vaut X », « calcule X », « X égale/= ? ». Quand elle est
# présente, le « x » entre deux nombres N'EST PLUS ambigu (l'utilisateur DEMANDE une multiplication) -> on le lit comme
# « × ». Sans cette intention, « x » reste un simple séparateur (« relais 4 x 100 m ») et n'est PAS converti (#82).
_CALC_INTENT = re.compile(
    r"\b(?:combien\s+(?:font|fait|valent|vaut|ca\s+fait)|calcul\w*|resou\w+|multipli\w+|"
    r"additionn\w+|soustrai\w+|divis\w+|modulo|\bmod\b|reste\s+de)\b|=\s*\??\s*$|\begale?\s*\??\s*$"
    r"|\d\s*(?:%|pour\s*cents?)\s+de\s+\d|\bau\s+carr[ée]\b|\bau\s+cube\b")


_CONV_UNITE = {"celsius": "C", "c": "C", "°c": "C", "fahrenheit": "F", "f": "F", "°f": "F",
               "kelvin": "K", "kelvins": "K", "°k": "K",
               "kilometre": "KM", "kilometres": "KM", "km": "KM", "mile": "MI", "miles": "MI",
               "kilogramme": "KG", "kilogrammes": "KG", "kilo": "KG", "kilos": "KG", "kg": "KG",
               "livre": "LB", "livres": "LB", "lb": "LB", "lbs": "LB"}
_CONV_RE = re.compile(
    r"(-?\d+(?:[.,]\d+)?)\s*(?:degr[ée]s?\s+)?°?\s*([a-zà-ÿ°]+)\s+en\s+(?:degr[ée]s?\s+)?°?\s*([a-zà-ÿ°]+)", re.I)


def _cap_conversion(texte: str):
    """CONVERSION D'UNITÉS FERMÉE et EXACTE : « convertis 100 degrés Celsius en Fahrenheit » -> 212 °F, formule
    montrée. Couples définis par des constantes LÉGALES exactes (°C↔°F ; 1 mile = 1,609344 km ; 1 lb =
    0,45359237 kg) — aucun arrondi caché : 4 décimales affichées au plus, formule re-vérifiable. Hors de la
    liste fermée -> None (jamais d'approximation inventée)."""
    m = _CONV_RE.search(texte)
    if not m:
        return None
    u1, u2 = _CONV_UNITE.get(_normalise(m.group(2))), _CONV_UNITE.get(_normalise(m.group(3)))
    if not u1 or not u2 or u1 == u2:
        return None
    v = float(m.group(1).replace(",", "."))
    aff = lambda x: ("%.4f" % x).rstrip("0").rstrip(".").replace(".", ",")
    if (u1, u2) == ("C", "F"):
        return "%s °C = %s °F  (formule exacte : (%s × 9/5) + 32)." % (aff(v), aff(v * 9 / 5 + 32), aff(v))
    if (u1, u2) == ("F", "C"):
        return "%s °F = %s °C  (formule exacte : (%s − 32) × 5/9)." % (aff(v), aff((v - 32) * 5 / 9), aff(v))
    if (u1, u2) == ("C", "K"):
        return "%s °C = %s K  (définition exacte : %s + 273,15)." % (aff(v), aff(v + 273.15), aff(v))
    if (u1, u2) == ("K", "C"):
        return "%s K = %s °C  (définition exacte : %s − 273,15)." % (aff(v), aff(v - 273.15), aff(v))
    if (u1, u2) == ("F", "K"):
        return "%s °F = %s K  (exact : (%s − 32) × 5/9 + 273,15)." % (aff(v), aff((v - 32) * 5 / 9 + 273.15), aff(v))
    if (u1, u2) == ("K", "F"):
        return "%s K = %s °F  (exact : (%s − 273,15) × 9/5 + 32)." % (aff(v), aff((v - 273.15) * 9 / 5 + 32), aff(v))
    if (u1, u2) == ("KM", "MI"):
        return "%s km = %s mile(s)  (1 mile = 1,609344 km, définition légale)." % (aff(v), aff(v / 1.609344))
    if (u1, u2) == ("MI", "KM"):
        return "%s mile(s) = %s km  (1 mile = 1,609344 km, définition légale)." % (aff(v), aff(v * 1.609344))
    if (u1, u2) == ("KG", "LB"):
        return "%s kg = %s livre(s)  (1 livre = 0,45359237 kg, définition légale)." % (aff(v), aff(v / 0.45359237))
    if (u1, u2) == ("LB", "KG"):
        return "%s livre(s) = %s kg  (1 livre = 0,45359237 kg, définition légale)." % (aff(v), aff(v * 0.45359237))
    return None


def _reponse_calcul(texte: str) -> str | None:
    """CALCUL DIRECT mono-question (« Combien font 4x10 ? » -> « 40 »). Tenté AVANT le repli web pour qu'une
    intention de calcul claire obtienne son résultat EXACT plutôt qu'une page web sans rapport. FAUX=0 : on ne
    renvoie que le verdict VÉRIFIÉ du moteur (entiers exacts) ; sinon None (abstention honnête, pas d'arrondi).
    Le « x » n'est converti en « × » QUE si l'intention de calcul est explicite (sinon « 4 x 100 » reste intact)."""
    if not _CALC_INTENT.search(_normalise(texte)):
        return None
    texte = re.sub(r"(?<=\d)[\s  ]+(?=\d{3}\b)", "", texte)   # milliers à espace (« 5 000 » lu 000, FAUX vécu)
    # NOMBRES EN LETTRES (« combien font douze fois huit ? ») : conversion FERMÉE, UNIQUEMENT sous intention de
    # calcul explicite (hors de ce contexte « un/six » resteraient des mots normaux). FAUX=0 : mapping exact.
    _MOTS_NB = {"zéro": "0", "zero": "0", "un": "1", "une": "1", "deux": "2", "trois": "3", "quatre": "4",
                "cinq": "5", "six": "6", "sept": "7", "huit": "8", "neuf": "9", "dix": "10", "onze": "11",
                "douze": "12", "treize": "13", "quatorze": "14", "quinze": "15", "seize": "16", "vingt": "20",
                "trente": "30", "quarante": "40", "cinquante": "50", "soixante": "60", "cent": "100",
                "mille": "1000"}
    # MODULO / RESTE EN PREMIER (FAUX=0 : « reste de 17 divisé par 5 » donnait 3.4 — la division ignorait
    # « reste ». Un reste est le MODULO, pas le quotient). « reste de X (divisé) par Y », « X modulo/mod Y ».
    _mod = (re.search(r"reste\s+de\s+(\d+)\s+(?:divis[ée]s?\s+par|par|sur)\s+(\d+)", texte, re.I)
            or re.search(r"\b(\d+)\s+(?:modulo|mod)\s+(\d+)\b", texte, re.I))
    if _mod:
        a, b = int(_mod.group(1)), int(_mod.group(2))
        return str(a % b) if b else None                # b=0 -> None (pas de reste défini, abstention honnête)
    # POURCENTAGE en PREMIER : « 20 % de 150 » / « 20 pour cent de 150 » -> 20 * 150 / 100 (= 30, précédence
    # gauche-droite). AVANT _MOTS_NB, qui transformerait « pour cent » en « pour 100 » et casserait le motif.
    texte = re.sub(r"(\d+(?:[.,]\d+)?)\s*(?:%|pour\s*cents?)\s+de\s+(\d+(?:[.,]\d+)?)",
                   r"\1 * \2 / 100", texte, flags=re.I)
    # NOMBRES COMPOSÉS D'ABORD (FAUX vécu 2026-07-08 : « vingt-sept » passait mot à mot -> « 20-7 » et le
    # trait d'union devenait une SOUSTRACTION — « quinze plus vingt-sept » rendait 28 au lieu de 42). Table
    # 0..100 générée par le MÊME générateur que « écris N en lettres » (ancres épinglées au banc), motifs les
    # plus longs d'abord, trait d'union ou espace acceptés (« vingt sept » = « vingt-sept »).
    texte = _remplace_nombres_lettres(texte)
    texte = re.sub(r"\b(" + "|".join(_MOTS_NB) + r")\b",
                   lambda mm: _MOTS_NB[mm.group(1).lower()], texte, flags=re.I)
    # OPÉRATEURS EN TOUTES LETTRES avec la VRAIE précédence (« 3 plus 4 fois 5 » -> 3 + 4 * 5 = 23, pas 35) :
    # _juge_arith évalue en précédence réelle. FERMÉ, uniquement sous intention de calcul (gate ci-dessus).
    texte = re.sub(r"(?<=\d)\s+divis[ée]s?\s+par\s+(?=\d)", " / ", texte, flags=re.I)
    texte = re.sub(r"(?<=\d)\s+(?:multipli[ée]s?\s+par|fois)\s+(?=\d)", " * ", texte, flags=re.I)
    texte = re.sub(r"(?<=\d)\s+plus\s+(?=\d)", " + ", texte, flags=re.I)
    texte = re.sub(r"(?<=\d)\s+moins\s+(?=\d)", " - ", texte, flags=re.I)
    # PUISSANCES fermées : « 7 au carré » -> 7 * 7 ; « 3 au cube » -> 3 * 3 * 3.
    texte = re.sub(r"(\d+(?:[.,]\d+)?)\s+au\s+carr[ée]\b", r"\1 * \1", texte, flags=re.I)
    texte = re.sub(r"(\d+(?:[.,]\d+)?)\s+au\s+cube\b", r"\1 * \1 * \1", texte, flags=re.I)
    # « x »/« × » collés ou espacés entre deux nombres -> « * » ESPACÉ (resout_arithmetique exige des espaces).
    p_math = re.sub(r"(?<=\d)\s*[x×]\s*(?=\d)", " * ", texte)
    try:
        import fonction_nl
        from base_faits import VERIFIE
        st, val, _ = fonction_nl.resout_arithmetique(p_math)
        if st == VERIFIE and val is not None:
            return str(val)
    except Exception:
        pass
    try:
        import classifieur_bornage as _CB
        v = _CB._juge_arith(_CB._norm(p_math))
        if v is not None:
            return str(int(v) if isinstance(v, float) and v.is_integer() else v)
        # repli : EXTRAIRE la sous-expression mathématique pure (« QUEL EST 20 * 150 / 100 ? » — le préfixe
        # interrogatif fait échouer les évaluateurs). On n'évalue que la course chiffres/opérateurs, fermée.
        mm = re.search(r"-?\d[\d\s+*/,.×-]*\d|\d", p_math)
        if mm and re.search(r"[+*/×-]", mm.group(0)):
            v = _CB._juge_arith(_CB._norm(mm.group(0).strip()))
            if v is not None:
                return str(int(v) if isinstance(v, float) and v.is_integer() else v)
    except Exception:
        pass
    return None


_NB_LETTRES_RE = None
_NB_LETTRES_VAL: dict = {}


def _remplace_nombres_lettres(texte: str) -> str:
    """Remplace les nombres en toutes lettres 0..100 par leurs chiffres, COMPOSÉS d'abord (« vingt et un »,
    « soixante-quinze », « quatre-vingt-dix-neuf »). Table auto-générée depuis fonction_nl._nombre_en_lettres
    (le générateur aux 13 ancres épinglées) -> une seule source de vérité orthographique."""
    global _NB_LETTRES_RE
    if _NB_LETTRES_RE is None:
        import fonction_nl as _FNL
        pats = []
        for n in range(0, 101):
            cle = re.sub(r"\s+", " ", _normalise(_FNL._nombre_en_lettres(n)))
            _NB_LETTRES_VAL[cle] = n
            pats.append(cle)
        pats.sort(key=len, reverse=True)
        alt = "|".join(r"[-\s]+".join(re.escape(tok) for tok in p.split()) for p in pats)
        _NB_LETTRES_RE = re.compile(r"\b(?:%s)\b" % alt, re.IGNORECASE)
    return _NB_LETTRES_RE.sub(
        lambda m: str(_NB_LETTRES_VAL.get(re.sub(r"\s+", " ", _normalise(m.group(0))), m.group(0))), texte)


def _ressemble_calcul(texte: str) -> bool:
    """La question ressemble-t-elle à un CALCUL non résolu (intention de calcul + au moins deux nombres) ? Sert de
    GARDE au repli web : on n'envoie PAS une opération arithmétique au métamoteur (qui renverrait une page produit
    contenant « 4x10 » au lieu d'abstenir). Purement protecteur : ne supprime jamais une vraie réponse factuelle."""
    if not _CALC_INTENT.search(_normalise(texte)):
        return False
    return len(re.findall(r"\d+", texte)) >= 2


def _reformule_synonymes(texte: str, conv_id: str | None) -> str | None:
    """Repli PARAPHRASE : sur échec du lookup exact, substitue un mot INCONNU de la base par un synonyme VALIDÉ
    (réseau JeuxDeMots) et re-vérifie. Renvoie le fait vérifié préfixé du signal de reformulation, ou None.
    FAUX=0 : la réponse reste un fait VÉRIFIÉ ; on ne substitue jamais un mot standard (garde anti-mauvais-sens) ;
    on signale honnêtement le mot compris. Ne tourne qu'en mode plein (base chargée)."""
    try:
        import synonymes as _SYN
    except Exception:
        return None
    if not _SYN.disponible():
        return None
    _vn, _pi, valides = _guerison()
    noms, verbes = valides if valides else (set(), set())
    connu = (lambda mn: mn in noms or _fait_forme_verbale(mn, verbes)) if (noms or verbes) else None
    try:
        variantes = _SYN.variantes_requete(texte, k_syn=3, max_variantes=8, est_connu=connu)
    except Exception:
        return None
    for var, _orig, syn in variantes:
        rep = _connaissance_verifiee(var, conv_id)
        if rep and not _reponse_incoherente_mesure(var, rep):
            return "%s  (en comprenant « %s »)" % (rep, syn)
    return None


def _multi_questions(texte: str, conv_id: str | None) -> str | None:
    """MULTI-DEMANDES dans une seule phrase (« capitale de la France ET nombre de continents ET 15 fois 3 »).
    NON-BLOQUANT : répond à CHAQUE sous-partie indépendamment, dit honnêtement « je ne l'ai pas » pour les inconnues,
    et combine le tout. SOUND (FAUX=0) : on n'engage le mode composé QUE si **au moins 2** sous-parties donnent un
    fait VÉRIFIÉ (sinon None -> pipeline normal ; protège les entités contenant « et » comme « Trinité-et-Tobago »)."""
    # GARDE SOMME COORDONNÉE (vécu 2026-07-08) : « 3 pièces de 2 euros et 2 billets de 5, combien en tout »
    # n'est PAS trois demandes — le « et » coordonne des quantités à SOMMER (route monnaie de fonction_nl).
    if re.search(r"\b(?:pi[eè]ces?|billets?)\s+de\s+\d", texte, re.IGNORECASE):
        return None
    # GARDE CONDITIONNELLE (vécu 2026-07-08) : « SI tous les chats sont gris ET QUE Félix est un chat… »
    # est UN raisonnement (prémisses liées), pas des demandes indépendantes — découper le détruit.
    if re.match(r"^\s*si\b", texte, re.IGNORECASE):
        return None
    # GARDE PROBLÈME D'HORLOGE (vécu 2026-07-08) : « le film commence à 21h ET dure 2h15, il finit à quelle
    # heure » n'est pas deux demandes — les heures énoncées + « quelle heure » = UN calcul (fonction_nl).
    if re.search(r"\d{1,2}\s*h\s*[0-5]?\d?\b", texte) and re.search(r"quelle\s+heure", texte, re.IGNORECASE):
        return None
    parts = [p.strip(" ?.!") for p in _COORD_RE.split(texte) if p and p.strip(" ?.!")]
    parts = [p for p in parts if len(p.split()) >= 2 or re.search(r"\d\s*[-+*/x×]\s*\d", p)]  # ≥2 mots OU un calcul
    if len(parts) < 2:
        return None
    resolus = [(p, _resout_partie(p)) for p in parts]
    if sum(1 for _, r in resolus if r) < 2 and len(parts) < 3:   # ≥2 faits OU ≥3 parties (liste évidente) -> engage
        return None
    lignes = [("• %s : %s" % (p, r)) if r else ("• %s : je ne l'ai pas encore en mémoire" % p)
              for p, r in resolus]
    return "Voici ce que je peux répondre :\n" + "\n".join(lignes)


# ————————————————————————————————— MULTI-TOURS (suivi du sujet, anaphore) —————————————————————————————————
# « Quelle est la capitale du Japon ? » -> « et sa monnaie ? » : le « sa » désigne le Japon. On mémorise le
# dernier SUJET par conversation et on le réinjecte quand la question est une CONTINUATION (possessif / « et … »).
_DERNIER_SUJET: dict = {}
_DERNIER_QUESTION: dict = {}       # dernière QUESTION résolue (pour la continuation « même attribut, nouvelle entité »)
# Possessifs SEULS (« sa monnaie ? » = continuation). NB : « sont » (verbe être) en faisait partie par erreur ->
# « Quels SONT les flauves de la France ? » était pris pour une continuation et réinjectait le sujet précédent
# (multi-tours type A : « Usain Bolt » -> « athlétisme »). Retiré : « sont » n'est pas un possessif.
_POSSESSIFS = frozenset("sa son ses leur leurs".split())
_DET_RE = r"(?:de la |de l['’]|du |des |la |le |les |l['’]|au |aux |un |une )"

# NÉGATION : « quelle N'EST PAS la capitale… », « quel pays N'est PAS en Europe », « pourquoi X N'a PAS… ». Un lookup
# positif répondrait le FAIT VRAI (« Paris ») à une question NÉGATIVE = FAUX. On ne sait pas énumérer « ce qui n'est
# PAS X » de façon sûre -> on s'abstient (HORS honnête). `qn` est normalisé (sans apostrophe : « n'est » -> « n est »).
_NEG_RE = re.compile(r"\bn(?:e)?\b[^?]*\b(?:pas|plus|jamais|aucune?|nulle?)\b")


def _est_negation(texte: str) -> bool:
    """La question est-elle NÉGATIVE (ne … pas/plus/jamais/aucun) ? Si oui, aucun lookup positif n'est valide."""
    return bool(_NEG_RE.search(_normalise(texte)))


def _negation_bloquante(texte: str) -> bool:
    """Vraie négation LOGIQUE à bloquer ? Non si la « négation » fait partie d'un TITRE d'œuvre réel (#88) — « qui a
    écrit On ne badine pas avec l'amour » (Musset) doit répondre, pas s'abstenir. Sound : on ne lève le blocage que si
    une clé EXACTE contenant la négation existe (titre) ; une vraie négation logique n'a pas de telle clé -> reste bloquée."""
    if not _est_negation(texte):
        return False
    try:
        import resolution
        if resolution.negation_fait_partie_entite(texte):
            return False                              # la négation EST un titre d'entité réel -> ne pas bloquer
    except Exception:
        pass
    return True


# GARDE CAUSALE : une question « Pourquoi X… » demande une RAISON, pas un fait par clé. Le moteur n'a pas de données
# de causes -> il doit ABSTENIR (« pourquoi le ciel est bleu » le fait déjà). Sans ce garde, une question CHARGÉE à
# présupposé faux (« Pourquoi Paris est-elle la capitale de l'Allemagne ? ») résout le lookup interne (« capitale de
# l'Allemagne » -> Berlin) et FUIT. On saute le factuel -> HORS. NB : on NE bloque PAS « comment » (« comment s'appelle
# la capitale de la France » = nom, légitime) ; seulement « pourquoi / pour quelle raison / comment se fait-il ».
_CAUSALE_RE = re.compile(r"^(?:pourquoi|pour\s+quelle\s+raison|comment\s+se\s+fait[- ]?il|comment\s+ca\s+se\s+fait|"
                         r"qu['e ]?\s*est[- ]?ce\s+qui\s+(?:explique|cause|fait\s+que))\b")


def _est_causale(texte: str) -> bool:
    """Question de RAISON (« pourquoi… ») — jamais un lookup factuel par clé -> abstention (le moteur n'a pas de causes)."""
    return bool(_CAUSALE_RE.match(_normalise(texte)))


def _nouvelle_entite(texte: str) -> str:
    """Continuation TYPE B = NOUVELLE entité, MÊME attribut que le tour précédent. Deux formes :
       • « et la France ? », « et pour le Brésil ? »  (entité directe) ;
       • « et celle de la France ? », « et celui du Brésil ? »  (anaphore EXPLICITE de l'attribut : celle/celui/ceux).
    Renvoie l'entité (str) ou '' si ce n'est pas une continuation simple (≤3 mots, sans possessif — un « et sa
    monnaie ? » nomme un attribut et relève du type A, géré par `_reformule`)."""
    low = texte.strip().lower().rstrip(" ?.!")
    low = re.sub(r"\s+(?:alors|donc|maintenant)$", "", low)        # « et la France alors ? » -> retire le remplisseur
    _de = r"(?:de la |de l['’]|du |des |de )"                       # « de » + contractions (du = de+le, des = de+les)
    # (a) anaphore explicite « celle/celui/ceux/celles de <entité> » (l'attribut est repris implicitement)
    m = re.match(rf"^et\s+(?:celle|celui|ceux|celles)\s+{_de}(.+)$", low)
    if not m:
        # (b) entité directe « et <dét> <entité> »
        m = re.match(rf"^et\s+(?:pour\s+|avec\s+|en\s+|dans\s+)?{_DET_RE}?(.+)$", low)
    if not m:
        return ""
    cand = m.group(1).strip()
    mots = cand.split()
    if (not cand or len(mots) > 3 or any(p in mots for p in _POSSESSIFS)
            or cand in {"celle-ci", "celui-ci", "ceux-ci", "celles-ci", "celle-la", "celui-la", "ca", "ça"}):
        return ""                                                  # démonstratif nu sans entité -> pas de type B
    # CASSE D'ORIGINE restituée (vécu 2026-07-08) : « et de CO2 ? » renvoyait « co2 » — or les formules
    # chimiques sont sensibles à la casse (H2O ≠ h2o), la continuation sur un calcul échouait.
    m2 = re.search(re.escape(cand), texte, re.IGNORECASE)
    return m2.group(0) if m2 else cand


def _sujet_de(texte: str) -> str:
    """Sujet (entité) d'une question = ce qui suit la dernière préposition (« capitale du JAPON » -> « japon »)."""
    m = re.search(r"\b(?:de la|de l'|de l|du|des|de|en|au|aux)\s+(.+?)[\s?]*$", texte.strip(), re.IGNORECASE)
    return m.group(1).strip() if m else ""


def _sujet_large(texte: str) -> str:
    """Sujet d'une question, patrons ÉLARGIS aux formes sans préposition finale : « où est né NAPOLÉON IER ? »,
    « qui est MARIE CURIE ? », « où se trouve TOKYO ? ». Sert à mémoriser le sujet pour les anaphores
    inter-tours (« il est mort quand ? »). '' si rien d'extractible."""
    s = _sujet_de(texte)
    if s:
        return s
    t = texte.strip()
    m = re.search(r"\b(?:née?s?|morte?s?|décédée?s?|succédé\s+à|précédé)\s+(.+?)[\s?]*$", t, re.I)
    if m:
        return m.group(1).strip()
    m = re.search(r"\bse\s+trouve(?:nt)?\s+(.+?)[\s?]*$", t, re.I)
    if m:
        return m.group(1).strip()
    m = re.match(r"^\s*qui\s+(?:est|était)\s+(.+?)[\s?]*$", t, re.I)
    if m:
        return _strip_article(m.group(1).strip())
    return ""


_VOLATIL_RE = re.compile(
    r"\b(actuel|actuelle|actuels|actuelles|actuellement|aujourd'?hui|maintenant|désormais|present|présentement|"
    r"current|latest|dernier|dernière|derniers|dernières|récent|récente|en ce moment|à ce jour|cette année|"
    r"en 20\d\d)\b", re.I)


# Une ANNÉE dans une question de CALCUL/CONVENTION n'est pas un marqueur de fraîcheur : « est-ce que 2024 est
# une année bissextile » et « écris 1984 en chiffres romains » partaient au WEB (extrait Wikipédia « 2024 »,
# l'album « 1984 » de Van Halen ! — vécu sur le .exe 62, web ON) alors que la réponse est un calcul exact local.
_PAS_FRAICHEUR_RE = re.compile(
    r"\b(bissextile|chiffres?\s+romains?|en\s+(?:toutes\s+)?lettres|modulo|\bmod\b|reste\s+de\s+\d|"
    r"nombre\s+de\s+jours|combien\s+de\s+jours|"
    r"est[- ]ce\s+que\s+\d|\d+\s+(?:est|sera)(?:[-\s]+t)?[-\s]+(?:il|elle|ce)\b|"
    r"\d+\s+est\s+(?:un\s+|une\s+)?(?:nombre\s+)?(?:premi[eè]re?|paire?|impaire?|divisible|multiple|carr[ée]))",
    re.I)


def _est_volatil(texte: str) -> bool:
    """Question à réponse POTENTIELLEMENT PÉRIMÉE dans la base statique (« président ACTUEL », « DERNIER
    vainqueur », « en 2026 ») : on préférera la source LIVE (fraîcheur) quand le web est autorisé. FAUX=0
    inchangé (la source live est vérifiée + attribuée ; repli sur la base si indisponible). GARDE : une année
    dans une question de CALCUL (bissextile, chiffres romains, parité…) n'est pas un marqueur de fraîcheur."""
    if _PAS_FRAICHEUR_RE.search(texte):
        return False
    return bool(_VOLATIL_RE.search(texte))


def _est_continuation(texte: str) -> bool:
    """La question s'appuie-t-elle sur le sujet précédent ? (possessif « sa/son… », ou commence par « et »)."""
    low = texte.strip().lower()
    toks = set(re.findall(r"[a-zàâäéèêëîïôöùûüç']+", low))
    return bool(toks & _POSSESSIFS) or low.startswith("et ") or low.startswith("et,")


# ALIAS DE RAPPEL : le rappel de dialogue est LEXICAL. « tu sais mon NOM ? » ne recouvre pas « je m'APPELLE Yohan ».
# On enrichit la requête de rappel avec les synonymes du même CHAMP sémantique (sans inventer : le rappel ne fait que
# citer un vrai énoncé de l'utilisateur). Groupes choisis sûrs (on évite les mots trop courants/génériques qui
# rapprocheraient des énoncés hors-sujet). Tokens normalisés (sans accent), comme l'index de `conversation`.
_GROUPES_ALIAS = (
    frozenset("nom prenom appelle appelles appeler appelles nomme surnom surnomme".split()),
    frozenset("habite habites reside residence domicile habiter".split()),
    frozenset("metier profession travaille boulot".split()),
    frozenset("aime adore adores prefere preferes passion".split()),
)


_RAPPEL_STOP = frozenset((
    "quel quelle quels quelles est sont le la les un une des du de d au aux en et ou qui que quoi mon ma mes "
    "ton ta tes son sa ses notre votre leur ce cette ces je tu il elle on nous vous me te se avec pour dans sur "
    "comment combien quand pourquoi c est appelle appelles nomme dis dit sais connais prefere preferee "
    "preferee preferees habite fait a ai as").split())


def _mots_contenu_rappel(texte: str) -> set:
    """Mots de CONTENU distinctifs d'un énoncé (pour classer un rappel par pertinence) : ≥3 lettres, hors
    mots-outils ET hors mots trop GÉNÉRIQUES du champ « préférences » (préféré/habite…) qui, partagés par
    plusieurs énoncés, ne distinguent pas. Ce qui reste : plat, film, couleur, chien, sport, ville…"""
    return {m for m in re.findall(r"[a-zà-ÿ]{3,}", _normalise(texte)) if m not in _RAPPEL_STOP}


def _expanse_rappel(texte: str) -> str:
    """Requête de rappel ENRICHIE des synonymes du champ sémantique présent (nom↔appelle…). Ne change PAS la
    sûreté : le rappel cite un énoncé réel de l'utilisateur, jamais une invention ; ceci améliore la PERTINENCE."""
    toks = set(_normalise(texte).split())
    extra = set()
    for grp in _GROUPES_ALIAS:
        if toks & grp:
            extra |= grp
    extra -= toks
    return f"{texte} {' '.join(sorted(extra))}".strip() if extra else texte


# POLITESSE (ensemble FERMÉ) : salutations / remerciements / adieux / « ça va ». Améliore l'UX (« Bonjour ! » ne doit
# pas devenir « C'est noté »). SOUND : aucune invention de fait ; ne se déclenche QUE si le message est ENTIÈREMENT
# de la politesse (tous les tokens dans le vocab) ou une locution figée -> jamais « Bonjour, quelle est la capitale ? ».
_SALUT = frozenset("bonjour salut bonsoir coucou hello hi hey allo".split())
_MERCI = frozenset("merci thanks".split())
_POLI_VOCAB = _SALUT | _MERCI | frozenset("beaucoup bien mille tres et toi vous le".split())
_LOC_ADIEU = ("au revoir", "a bientot", "a plus", "a tres bientot", "bonne nuit", "bonne soiree", "bonne journee",
              "bye", "goodbye", "good night", "see you")
_LOC_CAVA = ("ca va", "comment ca va", "comment vas tu", "comment allez vous", "comment tu vas", "tu vas bien",
             "comment ca va aujourd hui")
# Formes ANGLAISES courantes (« hello how are you? » partait en recherche web -> hors-sujet total). On y répond
# socialement, EN ANGLAIS, avec l'honnêteté sur la langue (Provara travaille surtout en français pour l'instant).
_LOC_CAVA_EN = ("how are you doing", "how is it going", "how s it going", "hows it going", "how are you",
                "how do you do", "what s up", "whats up")
_NOM_EN = ("what is your name", "what s your name", "whats your name")
_IDENT_EN = ("who are you",)
_PHRASES_EN = frozenset(_LOC_CAVA_EN + _NOM_EN + _IDENT_EN + ("bye", "goodbye", "good night", "see you",
                                                              "thank you"))


# — Réponse SOCIALE robuste : salutations / « ça va » / nom, même COMBINÉS et dans le désordre.
#   Sound : ne répond QUE si le message est PUREMENT social (aucun contenu factuel résiduel).
_NOM_PHRASES = ("comment t appelles tu", "comment t appeles tu", "comment tu t appelles", "comment tu t appeles",
                "quel est ton nom", "ton nom c est quoi", "c est quoi ton nom", "tu t appelles comment", "ton nom")
_IDENT_PHRASES = ("qui es tu", "tu es qui", "qui est tu", "presente toi", "c est quoi toi", "tu es quoi")
_FILLER_SOCIAL = frozenset("et toi vous stp svp s il te plait le la aussi alors donc bien tres beaucoup mille ok".split())
# SE PRÉSENTER : « je m'appelle X » / « moi c'est X »... -> saluer par le PRÉNOM, ne JAMAIS chercher X sur le web.
#   On ne prend QUE les tournures NON ambiguës (« je suis X » est exclu : « je suis fatigué » n'est pas un nom).
_INTRO_RE = re.compile(
    r"\b(?:je m'?appelle|je me nomme|on m'?appelle|appelle[-\s]moi|mon\s+(?:pr[ée]nom|nom)\s+(?:est|c'?est)|"
    r"moi\s+c'?est|my name is|call me)\s+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'’\-]{1,29})", re.I)
# garde-fou : mots qui NE sont pas un prénom (évite « moi c'est fatigué » -> « Bonjour Fatigué »).
_NON_PRENOM = frozenset("le la les un une des mon ton son ma ta sa mes tes ses pas plus tres bien mal ok "
                        "content contente ravi ravie enchante enchantee desole desolee fatigue fatiguee "
                        "ici la bon bonne the a an my your".split())


def _reponse_sociale(texte: str):
    """Message purement social (salutation/ça va/nom, combinés OK) -> réponse chaleureuse ; None sinon."""
    toks = _normalise(texte).replace("?", " ").replace("!", " ").replace(".", " ").split()
    if not toks:
        return None
    n = " " + " ".join(toks) + " "
    flags = {"salut": False, "cava": False, "nom": False, "ident": False, "merci": False, "adieu": False, "presente": False}
    m_intro = _INTRO_RE.search(texte)                 # l'utilisateur DONNE son prénom ?
    prenom = None
    if m_intro:
        cand = m_intro.group(1).strip(" .,!?'’’-")
        if len(cand) >= 2 and _normalise(cand) not in _NON_PRENOM:
            prenom = cand[:1].upper() + cand[1:]
    en = False                                        # une locution ANGLAISE a matché -> répondre en anglais
    groupes = ([(p, "adieu") for p in _LOC_ADIEU] + [(p, "nom") for p in _NOM_PHRASES + _NOM_EN]
               + [(p, "ident") for p in _IDENT_PHRASES + _IDENT_EN]
               + [(p, "cava") for p in _LOC_CAVA + _LOC_CAVA_EN] + [("thank you", "merci")])
    for phrase, cle in sorted(groupes, key=lambda x: len(x[0]), reverse=True):
        pad = " " + phrase + " "
        while pad in n:
            n = n.replace(pad, " "); flags[cle] = True
            en = en or phrase in _PHRASES_EN
    reste = []
    for w in n.split():
        if w in _SALUT: flags["salut"] = True; en = en or w in ("hello", "hi", "hey")
        elif w in _MERCI: flags["merci"] = True; en = en or w == "thanks"
        elif w not in _FILLER_SOCIAL: reste.append(w)
    if prenom:                                # « je m'appelle X » -> X est le prénom, PAS une requête à chercher
        consommes = set(_normalise(m_intro.group(0)).split())
        reste = [w for w in reste if w not in consommes]
        flags["presente"] = True
    if reste or not any(flags.values()):     # contenu factuel résiduel -> pas (que) social
        return None
    if flags["adieu"] and not (flags["salut"] or flags["cava"] or flags["nom"] or flags["ident"]):
        return "See you soon!" if en else "À bientôt !"
    if en:      # réponse EN ANGLAIS + honnêteté : le mode anglais complet est prévu, pas encore là (pas de promesse floue)
        parts = []
        if prenom: parts.append(("Hello %s! Nice to meet you." % prenom) if flags["salut"] else ("Nice to meet you, %s!" % prenom))
        elif flags["salut"]: parts.append("Hello!")
        if flags["cava"]: parts.append("I'm doing well, thank you \U0001F642.")
        if not prenom and flags["ident"]:                 # « who are you » mérite la présentation, pas juste le nom
            parts.append("I'm Provara, a local, sovereign assistant created by Yohan Fauck. I answer from a base "
                         "of verified facts (offline, no GPU) and I'd rather say I don't know than make things up.")
        elif not prenom and flags["nom"]: parts.append("My name is Provara.")
        if flags["merci"] and not parts: parts.append("You're welcome!")
        parts.append("For now I answer best in FRENCH (a full English mode is on the roadmap) — "
                     "try « capitale de l'Espagne » or « population du Japon ».")
        return " ".join(parts)
    parts = []
    if prenom: parts.append(("Bonjour %s, enchantée \U0001F642." % prenom) if flags["salut"] else ("Enchantée, %s \U0001F642." % prenom))
    elif flags["salut"]: parts.append(_varie("salut", texte, "Bonjour !"))
    if flags["cava"]: parts.append(_varie("cava", texte, "Je vais très bien, merci 🙂."))
    if not prenom and flags["ident"]: parts.append(_META_REPONSES["identite"])  # « qui es-tu » -> vraie présentation
    elif not prenom and flags["nom"]: parts.append("Je m'appelle Provara.")
    if flags["merci"] and not parts: parts.append("Avec plaisir !")
    parts.append(_varie("invite", texte, "Pose-moi une question et je te réponds avec ce que je sais."))
    return " ".join(parts)


_SEG_PHRASE_RE = re.compile(r"(?<=[.!?])\s+")
_SALUT_TETE_RE = re.compile(r"^\s*(bonjour|salut|bonsoir|coucou|hello|hi|hey)[ ,!]+(.{4,})$", re.I | re.S)


# CONJONCTION multi-entités : « quelle est la population de la France et de l'Allemagne ? » -> on répond pour
# CHAQUE entité (via le pipeline normal, chaque réponse vérifiée) puis on combine. Tête d'attribut FERMÉE (formes
# « la X de Y ») pour ne pas capter « différence de … entre X et Y » (déjà gérée) ni « point commun entre X et Y ».
_CONJ_HEADS = ("capitale", "population", "superficie", "monnaie", "langue officielle", "langue", "president",
               "hymne", "gentile", "drapeau", "continent", "altitude", "pib", "indicatif", "point culminant")
_CONJ_RE = re.compile(
    r"^\s*(?:quelles?\s+(?:est|sont)\s+)?(?:la\s+|le\s+|les\s+|l['’]\s*)?(" + "|".join(_CONJ_HEADS) + r")\s+"
    r"(de\s+.+?\s+et\s+.+?)\s*\??\s*$", re.I)


def _decoupe_conjonction(texte: str):
    """(tête, [entités]) si `texte` est « TÊTE de X et (de) Y [et Z] » avec ≥2 entités, sinon None. FAUX=0 :
    ne fait que DÉCOUPER une demande ; chaque sous-réponse reste vérifiée par le pipeline normal."""
    m = _CONJ_RE.match(texte)
    if not m:
        return None
    tete, tail = m.group(1), m.group(2).strip()
    tail = re.sub(r"^de\s+", "", tail, flags=re.I)   # retire le « de » de tête ; les morceaux gardent leur article
    bruts = re.split(r"\s*,\s*|\s+et\s+", tail)       # coupe sur «, » et « et »
    ents = [_strip_article(e.strip(" .?!")) for e in bruts if e and e.strip(" .?!")]
    ents = [e for e in ents if e]
    if len(ents) < 2 or len(ents) > 6:
        return None
    if any(len(e.split()) > 5 for e in ents):        # un morceau trop long n'est pas une entité -> on s'abstient
        return None
    return tete, ents


def _detache_salutation(texte: str):
    """Sépare une TÊTE purement sociale d'une vraie demande qui suit : (réponse_sociale, reste) ou (None, texte).
    Deux formes : segments de phrase sociaux en tête (« Bonjour comment vas-tu ? <demande> ») et simple mot de
    salutation collé (« Bonjour <demande> »). Le RESTE est conservé VERBATIM (casse/accents) pour le pipeline."""
    segs = [s for s in _SEG_PHRASE_RE.split(texte.strip()) if s.strip()]
    if len(segs) >= 2:
        i = 0
        while i < len(segs) and _reponse_sociale(segs[i]) is not None:
            i += 1
        if 0 < i < len(segs):
            return _reponse_sociale(" ".join(segs[:i])), " ".join(segs[i:]).strip()
    m = _SALUT_TETE_RE.match(texte)
    if m:
        reste = m.group(2).strip()
        if _reponse_sociale(reste) is None:               # le reste est une vraie demande, pas du social
            return _reponse_sociale(m.group(1)), reste
    return None, texte


def _politesse(texte: str) -> str | None:
    """Réponse polie à une salutation/remerciement/adieu/« ça va » — ou None si ce n'est pas (que) de la politesse."""
    r = _reponse_sociale(texte)
    if r is not None:
        return r
    n = _normalise(texte).strip()
    if not n or len(n.split()) > 6:
        return None
    if n in _LOC_CAVA or any(n.startswith(p) for p in _LOC_CAVA):
        return "Je fonctionne bien, merci ! Pose-moi une question et je réponds avec ce que je sais."
    if any(n == p or n.startswith(p) for p in _LOC_ADIEU):
        return "À bientôt !"
    toks = n.split()
    if not all(w in _POLI_VOCAB for w in toks):   # un mot hors-politesse -> vraie demande (« merci dis la capitale »)
        return None
    if toks[0] in _MERCI:
        return "Avec plaisir !"
    if toks[0] in _SALUT:                          # « bonjour », « salut à toi » — pas de question
        return "Bonjour ! Pose-moi une question et je te réponds avec ce que je sais."
    return None


# MÉTA sur l'assistant (ensemble FERMÉ) : identité / nom / nature / capacités / sources / fonctionnement. Un
# assistant conversationnel doit pouvoir dire HONNÊTEMENT qui il est. SOUND : réponses VRAIES sur ce moteur (programme
# local, répond depuis une base de faits vérifiés, s'abstient au doute) ; fullmatch sur le message normalisé -> ne se
# déclenche QUE sur une question méta PURE (« Sais-tu quelle est la capitale… » contient du factuel -> pas de match).
_META_PATRONS = [
    (re.compile(r"(?:qui es[- ]?tu|tu es qui|qui est tu|c est quoi toi|tu es quoi|presente toi)"), "identite"),
    (re.compile(r"(?:qui t['e ]?a (?:cree|creee|developpe|developpee|fait|concu|programme|code|construit|imagine)|"
                r"qui est ton (?:createur|auteur|developpeur|concepteur|createur)|"
                r"ton (?:createur|auteur|developpeur) c est qui|"
                r"par qui (?:as[- ]?tu|es[- ]?tu|a[- ]?t[- ]?il) ete (?:cree|creee|fait|developpe|programme)|"
                r"qui a (?:cree|creee|fait|developpe|code|concu|imagine) (?:provara|cette ia|ce (?:programme|projet|logiciel))|"
                r"c est qui (?:ton createur|qui t a cree))"), "createur"),
    (re.compile(r"(?:quel est ton nom|comment t['e ]?appelles?[- ]?tu|comment tu t['e ]?appelles|ton nom c est quoi|"
                r"tu t appelles comment)"), "nom"),
    (re.compile(r"(?:que sais[- ]?tu faire|que peux[- ]?tu faire|tu sais faire quoi|tu peux faire quoi|"
                r"quelles sont tes capacites|a quoi sers[- ]?tu|tu sers a quoi)"), "capacites"),
    (re.compile(r"(?:es[- ]?tu (?:une |un )?(?:ia|intelligence artificielle|robot|humain|humaine|machine|personne|"
                r"reel|reelle|vrai|vraie|chatbot|programme|ordinateur|bot))"), "nature"),
    (re.compile(r"(?:d ou viennent (?:tes|les) (?:informations|donnees|sources|infos)|quelles sont tes sources|"
                r"d ou (?:tu )?(?:tires|sors|viennent)[a-z ]*tes (?:infos|informations|donnees)|d ou viens tu)"), "sources"),
    (re.compile(r"(?:comment fonctionnes?[- ]?tu|comment tu fonctionnes|comment ca marche|comment marches?[- ]?tu)"),
     "fonctionnement"),
]
_META_REPONSES = {
    "identite": "Je suis Provara, un assistant conversationnel local et souverain, créé par Yohan Fauck "
                "(https://yohanfauck.fr/). Je réponds à partir d'une base de faits vérifiés (sans GPU, hors-ligne), "
                "et je préfère dire que je ne sais pas plutôt que d'inventer.",
    "createur": "J'ai été créé par Yohan Fauck. 👋 Découvre son travail — LinkedIn : "
                "https://www.linkedin.com/in/yohan-f-1102588a/ · Portfolio : https://yohanfauck.fr/",
    "nom": "Je m'appelle Provara. Je réponds à partir d'une base de faits vérifiés, et je préfère dire que je ne sais pas plutôt que d'inventer.",
    "capacites": "Je réponds à des questions factuelles (géographie, chimie, langues, conversions d'unités, etc.) "
                 "à partir de faits vérifiés, et je m'abstiens quand je n'ai pas l'information.",
    "nature": "Je suis un programme informatique (pas un humain) qui répond à des questions à partir d'une base de "
              "faits vérifiés. Je m'abstiens quand je ne sais pas.",
    "sources": "Mes réponses proviennent d'une base de faits vérifiés constituée hors ligne ; quand un fait n'y est "
               "pas, je le dis plutôt que de l'inventer.",
    "fonctionnement": "Je cherche la réponse dans une base de faits vérifiés ; si je la trouve je la donne, sinon "
                      "je m'abstiens — je ne devine jamais.",
}


# NB : la branche « sens » EXIGE « du mot » (« sens du mot X ») — sinon « le sens de la vie » (piège philosophique
# qui DOIT rester HORS) serait réécrit en « définition de vie ». « que veut dire/signifie X » couvre le sens sans « mot ».
_DEF_ALIAS_RE = re.compile(
    r"^\s*(?:qu['e ]?\s*veut\s+dire|qu['e ]?\s*veulent\s+dire|que\s+signifie(?:nt)?|"
    r"(?:la\s+)?signification\s+d[eu']\s+mot|(?:quel\s+est\s+)?(?:le\s+)?sens\s+d[eu']\s+mot)\s+"
    r"(?:le\s+|la\s+|l['e]\s*)?(.+?)\s*\??\s*$", re.IGNORECASE)


def _alias_definition(texte: str) -> str:
    """« que veut dire X » / « que signifie X » / « sens du mot X » -> « définition de X » (voie déjà fonctionnelle).
    Sound : ne réécrit que ces formulations de demande de SENS ; renvoie le texte inchangé sinon."""
    # GARDE CODE MORSE (vécu 2026-07-08) : « que signifie ... --- ... en morse » n'est pas une demande de
    # SENS de l'animal — les tokens points/traits partent au décodeur (fonction_nl).
    if re.search(r"(?:^|\s)[.\-]{2,}(?:\s|$)", texte):
        return texte
    m = _DEF_ALIAS_RE.match(texte)
    if m and m.group(1).strip():
        return f"définition de {m.group(1).strip()}"
    return texte


# VÉRIFICATION FACTUELLE OUI/NON : « X est-elle/il <REL> de <Y> ? » (ou l'inverse). On résout chaque côté comme une
# relation ; le côté qui RÉSOUT est le fait, l'autre est l'ENTITÉ AFFIRMÉE. Si la valeur vérifiée CONTIENT l'entité
# affirmée -> « Oui. » (sûr). Sinon -> None : le flux normal renvoie la VRAIE valeur (réfutation implicite) ou HORS —
# on ne CONFIRME JAMAIS un faux, et on ne dit JAMAIS « Non » (relations multi-valuées : « le français est-il une
# langue de la Suisse » serait faux en « Non »). Purement ADDITIF : n'ajoute que le « Oui » d'un fait vérifié.
_OUINON_RE = re.compile(r"^(.+?)\s+est[- ](?:elle|il|ce|elles|ils)\s+(.+?)\s*\??\s*$", re.IGNORECASE)
# ARTICLE DE TÊTE — gère les formes À ESPACE (« la France », « de la ») ET ÉLIDÉES contiguës (« l'euro », « d'Allemagne »,
# « de l'or ») : le `\s+` final ne s'appliquait qu'aux formes à espace -> « l'euro » n'était PAS dérabotté (#107).
_ART_LEAD_RE = re.compile(r"^(?:de\s+l[ae]s?\b\s*|de\s+l['’]\s*|[ld]['’]\s*|(?:le|la|les|l|un|une|des|du|de|d)\s+)",
                          re.IGNORECASE)


def _strip_article(s: str) -> str:
    return _ART_LEAD_RE.sub("", s.strip()).strip(" ?.!\"'«»")


def _oui_non(texte: str):
    """Confirme « Oui. » une assertion factuelle VÉRIFIÉE (« Paris est-elle la capitale de la France ? »), ou None.
    Sound : jamais de confirmation d'un faux (mismatch -> None -> flux normal), jamais de « Non » (multi-valué).
    Extensions 2026-07-08 : « est-ce que X est Y » (même logique) ; NÉGATION « X n'est pas Y(, si ?) » — si le
    vérifié CONTREDIT la négation -> « Si — X est bien Y » (confirmer un fait positif est sûr) ; si le vérifié
    diffère de l'affirmé -> le fait vérifié est servi TEL QUEL (réfutation implicite, jamais un « Non » sec)."""
    t = texte.strip()
    t = re.sub(r",?\s*(?:si|non|n['’]est[- ]ce\s+pas)\s*\?*\s*$", " ?", t, flags=re.IGNORECASE)  # « …, si ? »
    mneg = re.match(r"^\s*(?:est[- ]ce\s+qu[e'’]\s*)?(.+?)\s+n['’e]\s*est\s+pas\s+(.+?)\s*\??\s*$", t,
                    re.IGNORECASE)
    if mneg:
        gauche, droite = mneg.group(1).strip(), mneg.group(2).strip()
        # GARDE : une question négative OUVERTE (« QUELLE ville n'est pas la capitale… ») n'est pas une
        # vérification d'assertion -> prudence, flux normal (la garde négation globale s'applique).
        if re.match(r"^(quelle?s?|qui|quoi|lequel|laquelle|lesquel(?:le)?s|que|o[uù])\b",
                    _normalise(_strip_article(gauche))):
            return None
        vg = _connaissance_verifiee(gauche, None)
        vd = _connaissance_verifiee(droite, None)
        if bool(vg) == bool(vd):                      # 0 ou 2 côtés résolus -> prudence, flux normal
            return None
        valeur, affirme = (vg, droite) if vg else (vd, gauche)
        cote = gauche if vg else droite               # la phrase-relation (« la capitale de la France »)
        if _normalise(_strip_article(affirme)) == _normalise(_strip_article(valeur)):
            return "Si — %s est bien %s (vérifié)." % (affirme, cote)
        return "Ce que j'ai de vérifié : %s → %s." % (cote, valeur)
    mq = re.match(r"^\s*est[- ]ce\s+qu[e'’]\s*(.+?)\s+est\s+(.+?)\s*\??\s*$", t, re.IGNORECASE)
    if mq:
        gauche, droite = mq.group(1).strip(), mq.group(2).strip()
    else:
        m = _OUINON_RE.match(t)
        if not m:
            return None
        gauche, droite = m.group(1).strip(), m.group(2).strip()
    # PERF+SOUND : « est-ce que 2024 est … » — un NOMBRE n'est pas une entité à résoudre (chaque côté relance
    # tout le pipeline : 5 s mesurées) ; les routes de calcul en aval savent trancher (parité, bissextile…).
    if re.fullmatch(r"\d+(?:[.,]\d+)?", _strip_article(gauche)):
        return None
    vg = _connaissance_verifiee(gauche, None)        # conv_id=None : aucun effet de bord multi-tours
    vd = _connaissance_verifiee(droite, None)
    if not vg and not vd:                             # aucun côté ne résout -> flux normal
        return None
    if vg and vd:
        # LES DEUX résolvent (« l'EURO est-il la MONNAIE de l'Allemagne » : « euro » est aussi une entité résolvable).
        # Ce n'est PAS forcément ambigu (#107) : on confirme si l'ENTITÉ d'un côté ÉGALE la VALEUR vérifiée de l'autre
        # (euro == monnaie de l'Allemagne). Sinon (valeurs sans lien) -> None prudent. Sound : « le dollar est-il la
        # monnaie de l'Allemagne » -> dollar≠euro ET monnaie-de-l-allemagne(texte)≠valeur-de-dollar -> None.
        ng, nd = _normalise(_strip_article(gauche)), _normalise(_strip_article(droite))
        if ng == _normalise(_strip_article(vd)) or nd == _normalise(_strip_article(vg)):
            return "Oui."
        return None
    valeur, affirme = (vg, droite) if vg else (vd, gauche)
    # ÉGALITÉ STRICTE (#85+#93) : on confirme « Oui » SEULEMENT si l'assertion ÉGALE la valeur vérifiée, les deux
    # côtés débarrassés de leur article de tête. Un SOUS-MOT n'est PAS la réponse : « 2 » de « 26 » (#85), mais aussi
    # « Star » de « Star Alliance », « Candida » de « Candida albicans », « Amérique » de « Amérique du Sud » (#93 :
    # 2487 sur-confirmations partielles trouvées par chasseur). « la colombe »=« colombe » (article) confirme ;
    # l'assertion COMPLÈTE (« Star Alliance ») confirme. Sound (FAUX=0) : jamais de « Oui » à une réponse imprécise.
    na = _normalise(_strip_article(affirme))
    nv = _normalise(_strip_article(valeur))
    if na and na == nv:
        return "Oui."
    return None                                       # mismatch / partiel / multi-valué -> flux normal (vraie valeur ou HORS)


# DÉTECTEUR « ça ressemble à de l'ANGLAIS » : plutôt que d'envoyer une phrase anglaise dans le pipeline factuel
# français (qui répondait TOTALEMENT à côté via la recherche plein-texte), on DEMANDE une reformulation — la
# clarification honnête vaut mieux qu'une réponse hors-sujet. Mots-outils anglais SANS collision avec le français
# (« a », « an », « me », « on »… exclus). Seuil : ≥2 occurrences ET ≥40 % des tokens.
_TOKENS_EN = frozenset(
    "the is are was were you your how what who where when why which do does did can could would should "
    "please hello hi hey thanks thank of for with want need help make give tell know my we they i im it its "
    "this that have has had will would not dont cant isnt whats".split())
_MSG_ANGLAIS = ("I can already answer factual questions in English (« what is the capital of X », « the currency "
                "of Y »…). For anything else I'm still strongest in FRENCH — rephrase in French and I'll answer "
                "with verified facts. / Pour l'instant je comprends surtout le FRANÇAIS — reformule en français et "
                "je réponds avec du vérifié.")
def _semble_anglais(texte: str) -> bool:
    toks = _normalise(texte).split()
    if len(toks) < 2:
        return False
    hits = sum(1 for t in toks if t in _TOKENS_EN)
    return hits >= 2 and hits >= len(toks) * 0.4


def _meta_assistant(texte: str) -> str | None:
    """Réponse HONNÊTE à une question sur l'assistant lui-même (qui es-tu / tes capacités / tes sources…), ou None.
    SOUND : fullmatch sur le message normalisé -> ne capte JAMAIS une question factuelle (« sais-tu la capitale… »)."""
    n = _normalise(texte).strip()
    if not n or len(n.split()) > 9:
        return None
    for patron, cle in _META_PATRONS:
        if patron.fullmatch(n):
            rep = _META_REPONSES[cle]
            if cle == "sources":
                # REGISTRE DES SOURCES VÉRIFIÉES (enrichi 2026-07-08, demande Yohan « une liste complète ») :
                # la réponse méta LISTE le registre réel (sources.py, donnée pas code) au lieu du texte figé.
                try:
                    import sources as _SRCM
                    _acts = _SRCM.toutes(actives_seulement=True)
                    if _acts:
                        _noms = [s.get("nom", s.get("id", "?")) for s in _acts]
                        rep += (" Mon registre de confiance compte %d sources officielles ou structurées — "
                                "notamment %s…" % (len(_acts), ", ".join(_noms[:8])))
                except Exception:
                    pass
            return rep
    return None


def _reformule(texte: str, sujet: str) -> str:
    """Remplace l'anaphore par le sujet explicite : « et sa monnaie ? » + japon -> « monnaie de japon »."""
    low = texte.strip().rstrip("?").strip()
    mots = [w for w in low.split() if w.lower() not in (_POSSESSIFS | {"et"})]
    return f"{' '.join(mots).strip()} de {sujet}"


# Messages TERMINAUX NON-FACTUELS — constantes partagées : assistant_nl (porte unique) classe POSITIVEMENT chaque
# texte (HORS / clarification / supposition rapportée) au lieu d'un défaut « fait » (faille passe adverse 2026-07-03).
_MSG_INCONNU_PREFIXE = "Je n'ai pas l'information en mémoire pour l'instant"
_MSG_WEB_COUPE = ("Je n'ai pas l'information dans mes données locales — et l'accès à internet est coupé. "
                  "Réactive-le (bouton « 🌐 Internet » à gauche) et je lance une recherche sourcée.")
_MSG_NOTE = "C'est noté, je m'en souviendrai. Tu pourras me le redemander."
_MSG_REFUS = "D'accord — reformule ta question et je réponds."
_MSG_RAPPEL_PREFIXE = "D'après ce que tu m'as dit : "
_MSG_DYM_PREFIXE = "Je ne suis pas sûr du mot « "
_MSG_STRUCTURE_PREFIXE = "J'ai compris la structure de ta question"
_MSG_STRUCTURE_COURT_PREFIXE = "Même chose pour « "
_STRUCT_TOUR: dict = {}       # conv_id -> tour de la dernière abstention structurée : deux abstentions
                              # CONSÉCUTIVES ne répètent pas la formule complète (« Même chose pour… »)
_MSG_WEB_HINT = ("(L'accès à internet est coupé — réactive-le, bouton « 🌐 Internet » à gauche, "
                 "et je lance une recherche sourcée.)")
_WEB_HINT_VU: dict = {}       # conv_id -> True : le conseil « réactive internet » n'est donné qu'UNE fois par
                              # conversation (le répéter à chaque abstention sonnerait mécanique, pas humain)


def _avec_web_hint(msg: str, conv_id: str | None) -> str:
    """Ajoute le conseil « réactive internet » à `msg`, une seule fois par conversation."""
    if conv_id and _WEB_HINT_VU.get(conv_id):
        return msg
    if conv_id:
        _WEB_HINT_VU[conv_id] = True
    return f"{msg} {_MSG_WEB_HINT}"


def _utile(rep) -> bool:
    """Une réponse de REJEU (dévoilement / recadrage oral / pronom / continuation) vaut-elle d'être retenue ?
    Ni générique, ni aveu d'ignorance (sinon le rejeu court-circuite les étages suivants du texte ORIGINAL).
    Les abstentions STRUCTURÉES restent utiles (elles disent CE QUI est compris — mieux que le générique)."""
    if not rep or not isinstance(rep, str):
        return False
    if rep.startswith(_MSG_STRUCTURE_PREFIXE) or rep.startswith(_MSG_STRUCTURE_COURT_PREFIXE):
        return True
    if est_fallback(rep):
        return False
    try:
        import assistant_nl as _A
        pfx = tuple(p for p in (getattr(_A, "_PFX_HORS_FAIT", None), getattr(_A, "_PFX_INDECIDABLE", None),
                                getattr(_A, "_PFX_SATURATION", None), getattr(_A, "_PFX_PRECISER", None)) if p)
    except Exception:
        pfx = ()
    return not (pfx and rep.startswith(pfx))


def _varie(cle: str, graine: str, defaut: str) -> str:
    """Variante naturelle (module `formulation`) pour l'intention `cle`, ou `defaut` si indisponible. Déterministe."""
    try:
        import formulation
        v = formulation.varie(cle, graine)
        return v or defaut
    except Exception:
        return defaut


def _variantes(cle: str, defaut) -> list:
    try:
        import formulation
        opts = formulation.variantes(cle)
        return opts or [defaut]
    except Exception:
        return [defaut]


def est_fallback(s: str) -> bool:
    """Le texte est-il un message d'ABSENCE (rien trouvé / simple accusé de réception) ? Sert à l'enveloppe
    d'assistant_nl (porte unique) pour distinguer une vraie réponse d'un aveu d'ignorance. Robuste aux VARIANTES
    de formulation (l'accusé « noté » a plusieurs libellés désormais)."""
    return isinstance(s, str) and (
        s.startswith(_MSG_INCONNU_PREFIXE) or s == _MSG_WEB_COUPE
        or s.startswith(_MSG_STRUCTURE_PREFIXE)      # abstention ENRICHIE (structure reconnue, non ancrée)
        or s.startswith(_MSG_STRUCTURE_COURT_PREFIXE)   # sa forme COURTE (abstentions consécutives)
        or s == _MSG_NOTE or s in _variantes("note", _MSG_NOTE))


# ————— Brique « STRUCTURE RECONNUE mais NON ANCRÉE » (piste EGO #3 : on peut reconnaître une grammaire sans
# comprendre un mot — l'honnêteté sur cet écart est une INFORMATION, pas un échec). Quand toute la cascade a rendu
# HORS, on ne se contente plus d'un « je ne sais pas » générique : si la question PARSE en (relation connue R,
# entité E), on dit EXACTEMENT ce qui est compris (la structure « R de E ») et ce qui manque (aucun fait vérifié
# pour trancher). FAUX=0 : le message ne rapporte que des recherches réellement faites, jamais un fait. —————

# Relations-SONDE pour tester si une entité est ANCRÉE quelque part (clé d'au moins un fait vérifié) : pays
# (capitale/continent/monnaie/population/superficie), villes, noms communs (définitions), personnes (naissances).
# Liste BORNÉE et rapide : petits fichiers via _charge_direct (déjà cachés), gros via _lookup_cell (streaming,
# mémoïsé). Une absence ici ne « prouve » pas l'inexistence — les messages disent « je n'ai pas trouvé », pas
# « ça n'existe pas ».
_ANCRAGE_SONDE = ("capitale", "continent", "monnaie", "population_pays", "superficie",
                  "population_ville", "definition_nom", "annee_naissance_personne")


def _entite_ancree(entite: str):
    """(nom_affiché, contexte|None) si l'entité est la clé d'un fait vérifié d'une relation-sonde, sinon None.
    `contexte` = sa DÉFINITION vérifiée (tronquée) quand c'est la sonde qui a ancré — dire QUI est l'entité
    explique souvent POURQUOI le fait demandé n'existe pas (« Wakanda : royaume FICTIF » -> pas de capitale)."""
    # SEED CURÉ PRIORITAIRE : pour un mot seedé (« jupiter » -> planète), la présentation dit le genre CURÉ —
    # la définition Wiktionnaire brute peut être du bruit circulaire (« jupiter : exoplanète de taille
    # similaire à jupiter » !) qui ferait dire une absurdité dans l'abstention.
    try:
        import est_un as _E
        genre_seed = _E._seed().get(_normalise(_strip_article(entite)))
        if genre_seed:
            return (entite, _E._AFFICHE.get(genre_seed, genre_seed))   # forme accentuée (« planète »)
    except Exception:
        pass
    # VILLE CONNUE : se présenter comme telle (« berlin — ville d'Allemagne ») plutôt que par la définition
    # Wiktionnaire du nom commun homonyme (« berlin : paquet de fil arrêté par un nœud » !).
    try:
        cv = _charge_direct("pays_ville").get(_normalise(_strip_article(entite)))
        if cv:
            try:
                import realisation_fr as _RF
                de_p = _RF.de_pays(cv[1])
            except Exception:
                de_p = "de %s" % cv[1]
            return (cv[0], "ville %s" % de_p)
    except Exception:
        pass
    for rel in _ANCRAGE_SONDE:
        try:
            cell = _lookup_cell(rel, entite)
        except Exception:
            cell = None
        if cell and cell[1] is not None:
            ctx = None
            if rel == "definition_nom" and isinstance(cell[1], str):
                ctx = cell[1].strip()
                if len(ctx) > 110:                            # tronque au mot (lisibilité, pas de coupe brutale)
                    ctx = ctx[:110].rsplit(" ", 1)[0] + "…"
            return (cell[0], ctx)
    return None


# Mots qui trahissent un MIS-PARSE de l'« entité » (copule/inversion : « la capitale du wakanda est-elle grande »
# capturerait ent=« wakanda est-elle grande ») -> on s'abstient de la brique, le générique reprend.
_ENT_SUSPECTE_RE = re.compile(r"\b(est|sont|es|suis|etait|était|serait|seront|a-t|ont|il|ils|elle|elles|on)\b|[?]", re.I)

# 3e famille de structures pour l'abstention structurée : FAITS ciblés (naissance/mort/localisation), patrons
# fermés MIROIR des caps _cap_fait_personne/_cap_localisation — quand le cap n'a pas trouvé le fait.
_SNA_FAITS = (
    (re.compile(r"^\s*(?:où|ou)\s+(?:est|était)\s+née?s?\s+(.+?)\s*\??\s*$", re.I), "où est né %s"),
    (re.compile(r"^\s*quand\s+(?:est|était)\s+née?s?\s+(.+?)\s*\??\s*$", re.I), "quand est né %s"),
    (re.compile(r"^\s*(?:où|ou)\s+(?:est|était)\s+morte?s?\s+(.+?)\s*\??\s*$", re.I), "où est mort %s"),
    (re.compile(r"^\s*quand\s+(?:est|était)\s+morte?s?\s+(.+?)\s*\??\s*$", re.I), "quand est mort %s"),
    (re.compile(r"^\s*(?:où|ou)\s+se\s+trouve(?:nt)?\s+(.+?)\s*\??\s*$", re.I), "où se trouve %s"),
    (re.compile(r"^\s*dans\s+quel\s+pays\s+(?:est|se\s+trouve)\s+(.+?)\s*\??\s*$", re.I), "dans quel pays est %s"),
    (re.compile(r"^\s*sur\s+quel\s+continent\s+(?:est|se\s+trouve)\s+(.+?)\s*\??\s*$", re.I),
     "sur quel continent est %s"),
)


def _def_lisible(d: str) -> str:
    """« (univers de Marvel) royaume africain fictif. » -> « royaume africain fictif (univers de Marvel) » :
    le marqueur de registre Wiktionnaire passe en FIN, la définition se lit comme une phrase naturelle."""
    d = d.strip().rstrip(".")
    m = re.match(r"^\(([^)]{1,40})\)\s*(.+)$", d)
    return f"{m.group(2)} ({m.group(1)})" if m else d


def _structure_non_ancree(texte: str, conv_id: str | None = None) -> str | None:
    """Message « structure reconnue mais non ancrée » si `texte` parse en (relation CONNUE, entité) alors que
    toute la cascade factuelle a rendu HORS ; None sinon (le message générique reprend). Deux cas distingués :
    entité ancrée nulle part (la sonde n'a rien trouvé) vs entité CONNUE mais sans fait pour CETTE relation.
    Avec `conv_id`, l'échange CONTINUE à travers l'abstention : le sujet et la question sont mémorisés pour les
    enchaînements (« et sa population ? », « et du mordor ? ») — le sens est relationnel, une abstention aussi.
    Trois familles de structures reconnues : « R de E » (relation nominale), « qui a écrit/composé/… E »
    (créateur d'une œuvre, mêmes patrons FERMÉS que _cap_createur), et les FAITS ciblés (« où est né E ? »,
    « où se trouve E ? », « dans quel pays est E ? » — patrons fermés miroir des caps fait-personne/localisation)."""
    tete = part = quete = None
    m = _REL_DE_ENT_RE.match(texte)
    if m:
        tete, ent = m.group(1).strip(), m.group(2).strip(" ?.!\"'«»").strip()
        nt, ne = _normalise(tete), _normalise(ent)
        if (nt not in _attr_heads() or len(ne) < 2 or ne in _attr_heads() or ne in _NEST_SCAFFOLD
                or ne.isdigit() or len(ent.split()) > 6 or _ENT_SUSPECTE_RE.search(ent)):
            return None
    else:
        ent_aff = None
        for patron, _head, gabarit in _CREATEUR_RULES:
            mc = patron.match(texte.strip())
            if not mc:
                continue
            ent_aff = mc.group(1).strip().strip(" ?.!\"'«»")     # AVEC son article (« le necronomicon » : affichage)
            ent = _strip_article(ent_aff)                        # SANS article (sonde d'ancrage + état multi-tours)
            ne = _normalise(ent)
            if len(ne) < 2 or ne.isdigit() or len(ent.split()) > 8 or _ENT_SUSPECTE_RE.search(ent):
                return None
            mp = re.search(r"a été (\w+) par", gabarit)      # participe du gabarit (« écrit », « composé »…)
            part = mp.group(1) if mp else "créé"
            break
        if part is None:
            for patron, gabarit in _SNA_FAITS:               # 3e famille : fait ciblé (naissance/mort/lieu)
                mf = patron.match(texte.strip())
                if not mf:
                    continue
                ent_aff = mf.group(1).strip().strip(" ?.!\"'«»")
                ent = _strip_article(ent_aff)
                ne = _normalise(ent)
                if len(ne) < 2 or ne.isdigit() or len(ent.split()) > 6 or _ENT_SUSPECTE_RE.search(ent):
                    return None
                quete = gabarit % ent_aff
                break
            if quete is None:
                return None
    tour = _PROFONDEUR.get(conv_id, 0) if conv_id else 0
    consecutif = bool(conv_id) and _STRUCT_TOUR.get(conv_id) == tour - 1
    prec = _DERNIER_SUJET.get(conv_id) if conv_id else None      # sujet du tour précédent (AVANT écrasement)
    if conv_id:
        _DERNIER_SUJET[conv_id] = ent
        _DERNIER_QUESTION[conv_id] = texte
        _STRUCT_TOUR[conv_id] = tour
    ancre = _entite_ancree(ent) or (None if tete else _entite_ancree(ent_aff))   # titres stockés avec article
    libelle = (f"{tete} de {ent}") if tete else (f"qui a {part} {ent_aff}" if part else quete)
    if ancre:
        affiche, ctx = ancre
        if tete:
            libelle = f"{tete} de {affiche}"
        if consecutif:                            # 2 abstentions d'affilée : on ne récite pas la formule complète
            # la présentation de l'entité ne se répète que si elle a CHANGÉ depuis le tour précédent.
            qui = f" ({_def_lisible(ctx)})" if (ctx and (not prec or _normalise(prec) != ne)) else ""
            return (f"{_MSG_STRUCTURE_COURT_PREFIXE}{libelle} »{qui} : là non plus, aucun fait "
                    f"vérifié pour trancher, je m'abstiens.")
        qui = (f"je connais « {affiche} » — {_def_lisible(ctx)} —" if ctx
               else f"je connais « {affiche} » (des faits vérifiés l'ancrent)")
        if tete:
            return (f"{_MSG_STRUCTURE_PREFIXE} — « {libelle} » : {qui} et je connais la relation "
                    f"« {tete} », mais je n'ai pas de fait vérifié « {tete} de {affiche} » qui me permette de "
                    f"trancher. Plutôt que d'inventer, je m'abstiens.")
        if part:
            return (f"{_MSG_STRUCTURE_PREFIXE} — « {libelle} » : {qui} mais aucun fait vérifié n'en désigne "
                    f"le créateur. Plutôt que d'inventer, je m'abstiens.")
        return (f"{_MSG_STRUCTURE_PREFIXE} — « {libelle} » : {qui} mais aucun fait vérifié ne me permet "
                f"d'y répondre. Plutôt que d'inventer, je m'abstiens.")
    if consecutif:
        return (f"{_MSG_STRUCTURE_COURT_PREFIXE}{libelle} » : là non plus, aucun fait vérifié pour "
                f"trancher, je m'abstiens.")
    if tete:
        return (f"{_MSG_STRUCTURE_PREFIXE} — « {libelle} » : je connais la relation « {tete} », mais je n'ai "
                f"trouvé aucun fait vérifié qui ancre « {ent} » dans mes données. Plutôt que d'inventer, je m'abstiens.")
    return (f"{_MSG_STRUCTURE_PREFIXE} — « {libelle} » : je comprends la %s, mais je n'ai trouvé aucun fait "
            f"vérifié qui ancre « {ent} » dans mes données. Plutôt que d'inventer, je m'abstiens."
            % ("demande (le créateur d'une œuvre)" if part else "question"))


def _build_id() -> str:
    """Identité du BUILD (commit tamponné dans VERSION_BUILD.txt par le workflow CI / build_exe.bat). Répond à
    « QUEL .exe est-ce que je teste ? » — un artifact périmé ne se distingue pas à l'œil. « source » hors .exe
    (sans lire le fichier : un reliquat de build local afficherait un tampon périmé)."""
    import sys
    if not getattr(sys, "frozen", False):
        return "source"
    racine = getattr(sys, "_MEIPASS", _HARNAIS)
    try:
        with open(os.path.join(racine, "VERSION_BUILD.txt"), "rb") as f:
            brut = f.read().decode("utf-8", "ignore")
        propre = "".join(c for c in brut if c.isalnum() or c in "._-")
        return propre[:12] or "?"
    except Exception:
        return "source"


def _diagnostic_connaissance(texte: str):
    """« diagnostic » / « combien de faits connais-tu » -> état RÉEL de la connaissance chargée (nb relations/faits +
    d'où viennent les données). Sert à vérifier que Provara a bien accès à sa base (utile pour déboguer le .exe)."""
    n = _normalise(texte).strip()
    # « combien DE faits/relations » exigé : la sous-chaîne nue capturait « ça FAIT combien, 12 fois 8 ? ».
    if not (n == "diagnostic" or re.search(r"combien\s+de\s+(?:relations?|faits?|choses?)\b", n)):
        return None
    try:
        import os, time as _tm, lecteur
        _t0 = _tm.perf_counter()
        _charge_ia()
        _t_charge = _tm.perf_counter() - _t0
        # CAPACITÉS PROUVÉES EN DIRECT (audit câblage 2026-07-06 : le registre capacites.py — 228 preuves à
        # réponse connue sur ~170 modules de raisonnement — n'était atteignable par RIEN dans le produit).
        # Chaque preuve est RÉELLEMENT exécutée à l'instant (<1 s, sans chargement de base) : couverture
        # MESURÉE au moment où l'utilisateur demande, jamais déclarée.
        cap = ""
        _t_preuves = 0.0
        try:
            import capacites as _CAP
            _t1 = _tm.perf_counter()
            # WATCHDOG par preuve (vécu .exe 2026-07-08 : une preuve bloquante gelait le diagnostic entier
            # sans nommer le coupable) : 10 s max par preuve, la bloquée est DÉSIGNÉE dans la réponse.
            _ok, _ko, _echecs = _CAP.verifie_tout(budget_par_preuve=10.0)
            _t_preuves = _tm.perf_counter() - _t1
            # Preuves LENTES servies du mémo de préchauffage (exécution réelle de ce processus, datée) :
            # l'affichage le DIT — « prouvées à l'instant » ne doit jamais mentir sur la fraîcheur.
            _memo = getattr(_CAP, "MEMO_UTILISES", [])
            _dont = ""
            if _memo:
                _age_min = max(0, int((_tm.time() - min(ts for _, ts in _memo)) / 60))
                _dont = " (dont %d au préchauffage, il y a %d min)" % (len(_memo), _age_min)
            cap = " · capacités prouvées : %d/%d%s%s" % (
                _ok, _ok + _ko, _dont, "" if not _echecs else " (en échec : %s)" % ", ".join(_echecs[:3]))
        except Exception:
            pass
        appris = ""
        try:
            import faits_appris as _FA
            _n = _FA.nombre_appris()
            if _n:
                appris = " · %d fait(s) appris du web (structurés, réutilisables hors-ligne)" % _n
        except Exception:
            pass
        routage = ""
        try:
            import tronc as _TRD
            _tot, _hors, _prof = _TRD.stats_routage()
            if _tot:
                routage = (" · routage par acte : %d décision(s), %d hors-famille, profondeur de sonde "
                           "moyenne %.1f cap(s)" % (_tot, _hors, _prof))
                import sequenceur as _SQD
                _SQD.recharge()                          # diagnostic = point d'observation : politique FRAÎCHE
                _appris = _SQD.rapport()
                if _appris:
                    _n_appris = sum(len(v) for v in _appris.values())
                    routage += " · séquenceur : %d cap(s) appris sur %d acte(s)" % (_n_appris, len(_appris))
                _ctot, _ccouv = _SQD.couverture()
                if _ctot:
                    routage += " (couverture prior %d%%)" % round(100 * _ccouv / _ctot)
        except Exception:
            pass
        # INVENTAIRE À BUDGET (vécu .exe 2026-07-08 : le diagnostic partait en timeout — compter 72 M de
        # faits force le chargement de TOUTES les tables ; sur données froides, ça peut durer des minutes).
        # Budget 10 s : au-delà, le compte partiel est rendu HONNÊTEMENT (« au moins N ») et l'inventaire
        # progresse au diagnostic suivant (les tables chargées restent chargées).
        _t2 = _tm.perf_counter()
        _lim = _t2 + 10.0
        n_faits, complet = 0, True
        for _tab in lecteur.LECTEUR.tables.values():
            n_faits += len(_tab)
            if _tm.perf_counter() > _lim:
                complet = False
                break
        _t_inv = _tm.perf_counter() - _t2
        aff_faits = ("%d fait(s)" % n_faits) if complet else \
            ("au moins %d faits (inventaire complet interrompu à 10 s — il reprendra au prochain diagnostic)"
             % n_faits)
        return ("Diagnostic : je connais %d relation(s) et %s. Données : %s · build %s · recherche web %s%s%s%s"
                " · étapes : chargement %.1f s, preuves %.1f s, inventaire %.1f s"
                % (len(lecteur.LECTEUR.relations()), aff_faits,
                   os.environ.get("LECTEUR_DATASETS_DIR", "?"), _build_id(),
                   "activée" if os.environ.get("IA_WEB") == "1" else "désactivée", cap, appris, routage,
                   _t_charge, _t_preuves, _t_inv))
    except Exception as e:
        return "Diagnostic : impossible de lire l'\u00e9tat de la base (%s)" % e


_WEB_MODULE_SIGNALE = False   # échec d'import de la recherche web déjà affiché ? (une fois, pas à chaque question)
_PREF_LANGUE: dict = {}       # conv_id -> code langue préféré (« réponds en X ») pour les tours suivants
_PREF_LANGUE_GLOBAL = [None]  # préférence GLOBALE posée par le sélecteur de l'interface (/api/langue)


_OUINON_Q_RE = re.compile(
    r"^\s*est[- ]ce\s+qu"                                    # « est-ce que / qu' … »
    r"|\b[a-zà-ÿ]+[- ]t[- ](?:il|elle|ils|elles|on)\b"        # « a-t-il », « peut-elle », « possède-t-il »
    r"|\b(?:est|sont|a|ont|as|peut|peuvent|possede|possedent|contient|contiennent|fait|font)"
    r"[- ](?:il|elle|ils|elles|ce)\b", re.I)


def _question_oui_non(texte: str) -> bool:
    """La question est-elle FERMÉE (oui/non) ? « est-ce que … », « X a-t-il … », « X est-elle … ». Sert à ne PAS
    servir un rapport web en texte libre (souvent hors-sujet) à une question qui attend « oui »/« non »."""
    return bool(_OUINON_Q_RE.search(texte))


def _extrait_pertinent(question: str, titre: str, extrait: str) -> bool:
    """GATE DE QUALITÉ des rapports web : un extrait n'est servi que s'il PARLE de ce qui est demandé. Le
    métamoteur matche parfois UN mot isolé (« capitale du wakanda » -> page gentilés « habitants de Wakanda »
    sans un mot sur la capitale) : servir ça, même attribué, est du bruit. Structure reconnue (R de E) ->
    la RELATION et l'ENTITÉ doivent toutes deux apparaître dans titre+extrait ; sinon ≥60 % des mots de
    contenu de la question. FAUX=0 renforcé : mieux vaut l'abstention structurée qu'un hors-sujet sourcé."""
    corpus = _normalise("%s %s" % (titre or "", extrait or ""))
    m = _REL_DE_ENT_RE.match(question)
    if m and _normalise(m.group(1).strip()) in _attr_heads():
        tete = _normalise(m.group(1).strip())
        ent_mots = re.findall(r"[\wà-ÿ]{3,}", _normalise(m.group(2).strip(" ?.!\"'«»")))
        return tete in corpus and all(w in corpus for w in ent_mots)
    mots = [w for w in re.findall(r"[\wà-ÿ]{4,}", _normalise(question))
            if w not in _NEST_SCAFFOLD and w not in _GENERIQUES]
    if not mots:
        return True
    present = sum(1 for w in mots if w in corpus)
    return present * 5 >= len(mots) * 3


def _recherche_structuree(question: str):
    """Le lecteur n'a rien -> SOURCE STRUCTURÉE fiable (Wikidata), réponse VÉRIFIÉE + ATTRIBUÉE (FAUX=0).
    Extraction SPARQL déterministe, jamais du texte libre. Réseau requis (opt-in IA_WEB=1). None si rien/erreur."""
    global _WEB_MODULE_SIGNALE
    try:
        import veille_structure
    except Exception as e:
        if not _WEB_MODULE_SIGNALE:      # console = seul canal de diagnostic du .exe -> jamais silencieux
            _WEB_MODULE_SIGNALE = True
            try:                          # un print qui échoue (console exotique) ne doit pas casser la réponse
                print("  [Provara] ⚠ recherche web INDISPONIBLE (import veille_structure) : %r" % e, flush=True)
            except Exception:
                pass
        return None
    try:
        res = veille_structure.interroge_nl(question)          # source FIABLE (Wikidata) -> fait vérifié
    except Exception:
        res = None
    if res:
        _, _, valeur, source = res
        return "%s  (trouvé sur %s)" % (valeur, source)
    # GARDE OUI/NON : une question fermée (« est-ce que la bagnole a 4 roues ? ») ne se répond PAS par un rapport
    # web en TEXTE LIBRE — le métamoteur renvoie un article qui matche un mot-clé (« bagnole » -> film « Cars »),
    # totalement hors-sujet. On préfère l'ABSTENTION honnête au bavardage. La source structurée (Wikidata,
    # `interroge_nl` ci-dessus) reste autorisée car elle rend un fait, pas du texte libre.
    if _question_oui_non(question):
        return None
    try:
        wl = veille_structure.cherche_web_libre(question)      # web LIBRE (Wikipédia) -> rapport attribué + lien
    except Exception:
        wl = None
    try:                                                       # MULTI-SOURCES : domaines INDÉPENDANTS (métamoteur)
        autres = veille_structure.cherche_web_domaines(question)
    except Exception:
        autres = []
    # GATE DE PERTINENCE : un extrait qui ne parle pas de ce qui est demandé (match sur un mot isolé) n'est
    # pas servi — l'abstention structurée en aval dit davantage qu'un hors-sujet sourcé.
    if wl and not _extrait_pertinent(question, wl[1], wl[0]):
        wl = None
    autres = [a for a in (autres or []) if _extrait_pertinent(question, a[0], a[1])]
    if wl:
        extrait, titre, url = wl
        externes = [a for a in autres if not a[3].endswith("wikipedia.org")]
        lignes = ["D'après Wikipédia (« %s ») : %s" % (titre, extrait[:420]), "",
                  "\U0001F517 En savoir plus : %s" % url]
        if externes:                                           # ≥2 domaines parlent du sujet -> on le MONTRE
            lignes.append("\U0001F310 D'autres sources en parlent : "
                          + " · ".join("%s (%s)" % (a[3], a[2]) for a in externes))
            lignes.append("(Information trouvée sur internet, à vérifier au besoin.)")
        else:                                                  # une seule source -> le DIRE (honnêteté)
            lignes.append("(Source unique — information trouvée sur internet, à vérifier.)")
        return "\n".join(lignes)
    if autres:                                                 # pas de Wikipédia pertinente -> rapport métamoteur
        titre, extrait, url, dom = autres[0]
        lignes = ["D'après %s (« %s ») : %s" % (dom, titre, extrait), "",
                  "\U0001F517 En savoir plus : %s" % url]
        if len(autres) > 1:
            lignes.append("\U0001F310 Aussi sur : " + " · ".join("%s (%s)" % (a[3], a[2]) for a in autres[1:]))
        lignes.append("(Information trouvée sur internet, à vérifier au besoin.)")
        return "\n".join(lignes)
    return None


def _schema(entite: str):
    """Graphe SVG en étoile de ce que Provara CONNAÎT sur `entite` (relations réelles du lecteur). Renvoie une chaîne
    SVG (contrôlée, labels échappés) ou None. FAUX=0 : chaque arête = un fait réel du graphe, jamais inventé."""
    import math, html
    try:
        import ia
        aretes = ia.voisins(entite)
    except Exception:
        return None
    if not aretes:
        return None
    def lisible(rel):
        return not any(x in rel for x in ("code_", "iso", "identifiant", "_id_", "numero_", "matricule"))
    aretes = [(rel, aff) for rel, _val, aff in aretes if lisible(rel)][:10]
    if not aretes:
        return None
    W, H, R = 660, 470, 165
    cx, cy = W / 2, H / 2
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
           'style="max-width:100%%;background:#fbfbfe;border:1px solid #e5e7eb;border-radius:10px">' % (W, H, W, H)]
    n = len(aretes)
    for i, (rel, aff) in enumerate(aretes):
        a = 2 * math.pi * i / n - math.pi / 2
        x, y = cx + R * math.cos(a), cy + R * math.sin(a)
        out.append('<line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" stroke="#cbd5e1" stroke-width="1.5"/>' % (cx, cy, x, y))
        out.append('<text x="%.0f" y="%.0f" font-size="9" fill="#94a3b8" text-anchor="middle">%s</text>'
                   % ((cx + x) / 2, (cy + y) / 2 - 3, html.escape(rel.replace("_", " ")[:22])))
        out.append('<rect x="%.0f" y="%.0f" width="118" height="30" rx="7" fill="#eef2ff" stroke="#c7d2fe"/>'
                   % (x - 59, y - 15))
        out.append('<text x="%.0f" y="%.0f" font-size="11" fill="#3730a3" text-anchor="middle">%s</text>'
                   % (x, y + 4, html.escape(str(aff)[:20])))
    out.append('<circle cx="%.0f" cy="%.0f" r="48" fill="#4f46e5"/>' % (cx, cy))
    out.append('<text x="%.0f" y="%.0f" font-size="15" fill="#fff" text-anchor="middle" font-weight="bold">%s</text>'
               % (cx, cy + 5, html.escape(str(entite).strip()[:18])))
    out.append('</svg>')
    return "".join(out)


_SCHEMA_TRIG = re.compile(r"\b(montre|dessine|sch[ée]ma|graphe|que\s+sais[- ]?tu|sais[- ]?tu\s+sur)\b", re.I)


def _demande_schema(texte: str):
    """« montre-moi ce que tu sais sur X » / « schéma de X » / « graphe de X » -> SVG, ou None."""
    if not _SCHEMA_TRIG.search(texte):
        return None
    m = re.search(r"(?:\bsur\b|\bde\s+la\b|\bde\s+l['’]|\bdu\b|\bdes\b|\bde\b|\bd['’])\s+(.+?)\s*\??\s*$",
                  texte, re.I)
    ent = m.group(1).strip() if m else None
    if not ent:
        m2 = re.search(r"(?:montre|dessine|sch[ée]ma|graphe)\s+(?:moi\s+)?(.+?)\s*\??\s*$", texte, re.I)
        ent = m2.group(1).strip() if m2 else None
    if ent:
        ent = re.sub(r"^(?:la|le|les|l['’]|un|une|du|des|de|d['’])\s+", "", ent, flags=re.I).strip()
    if not ent or len(ent) < 2:
        return None
    return _schema(ent)


# ————————————————————————— CAPACITÉS OUTILS câblées au chat (2026-07-03, audit orphelines) —————————————————————————
# Des capacités RÉELLES de ia.py étaient injoignables depuis le dialogue. On les branche ici par intention
# explicite, en amont du factuel. FAUX=0 : chaque handler s'abstient (None ou message honnête) hors de son
# périmètre garanti — jamais de réponse inventée.
def _cap_grammaire(texte: str):
    """« nature (grammaticale) du mot X » -> classe + genre ; « analyse grammaticale : phrase » -> analyse.
    Léger (grammaire_fr, pas de lecteur). Abstention honnête si la nature est incertaine (jamais devinée)."""
    m = re.match(r"^\s*(?:quelle?\s+est\s+la\s+)?(?:nature|classe|cat[ée]gorie)\s+(?:grammaticale?\s+)?"
                 r"(?:du\s+(?:mot|vocable|terme)\s+|de\s+l['’]|de\s+la\s+|de\s+|d['’])\s*['\"«]?\s*"
                 r"([\wà-ÿ][\wà-ÿ'\-]*)\s*['\"»]?\s*\??\s*$",
                 texte, re.I)
    if m:
        try:
            import grammaire_fr as _G
        except Exception:
            return None
        mot = m.group(1)
        cl = _G.classe_mot(mot)
        if cl == "inconnu":
            return ("Je ne suis pas certain de la nature grammaticale de « %s » — je préfère ne pas deviner." % mot)
        g = _G.genre_mot(mot)
        return "« %s » : %s%s." % (mot, cl, (" (%s)" % g if g else ""))
    if "grammatical" in _normalise(texte):
        # forme « analyse grammaticale : PHRASE » (tête) OU « PHRASE, analyse grammaticale » (queue)
        m = re.match(r"^\s*analyse\s+(?:grammaticale(?:ment)?\s+)?(?:la\s+phrase\s+|cette\s+phrase\s*[:\-]?\s*)?(.+)$",
                     texte, re.I)
        phrase = m.group(1) if m else None
        if not phrase:
            m2 = re.match(r"^(.+?)[,;:\-]?\s*analyse\w*\s+grammaticale(?:ment)?\s*[.?!]*\s*$", texte, re.I)
            phrase = m2.group(1) if m2 else None
        if phrase and len(phrase.split()) >= 2:
            try:
                import grammaire_fr as _G
            except Exception:
                return None
            return _G.resume_analyse(phrase.strip(" :\"'«».?!"))
    return None


def _cap_conjugaison(texte: str):
    """« conjugue le verbe X » / « conjugaison de X » -> table du présent. FAUX=0 : abstention honnête hors du
    périmètre garanti (verbes réguliers 1er/2e groupe, présent) plutôt qu'une forme fausse."""
    if not (re.search(r"\bconjug(?:ue|ues|uer|aison)\b", texte, re.I)
            or re.search(r"\b(?:imparfait|pr[ée]sent|futur)\s+d[e'’]", texte, re.I)):
        return None
    # ⚠ le verbe demandé n'est PAS « conjuguer » lui-même (« comment CONJUGUER aimer » conjuguait
    # « conjuguer », FAUX vécu 2026-07-08) ; un TEMPS hors présent -> honnêteté, jamais le présent servi
    # en silence à la place du futur demandé.
    mt = re.search(r"\b(imparfait|futur|pass[ée]\s+(?:compos[ée]|simple)|conditionnel|subjonctif)\b", texte, re.I)
    if mt:
        return ("Je ne conjugue de façon SÛRE que le PRÉSENT des verbes réguliers du 1er/2e groupe — le %s "
                "sort de ce périmètre garanti et je préfère m'abstenir que risquer une forme fausse."
                % mt.group(1).lower())
    m = re.search(r"\b(?!conjugu)([a-zàâäéèêëïîôöùûüç]+(?:er|ir|re))\b", texte, re.I)
    if not m:
        return None
    inf = m.group(1).lower()
    try:
        import conjugaison as _C
        formes = [_C.conjugue(inf, p, "present") for p in range(1, 7)]
    except Exception:
        return ("Je ne conjugue de façon SÛRE que les verbes réguliers du 1er/2e groupe au présent ; « %s » "
                "sort de ce périmètre garanti et je préfère m'abstenir que risquer une forme fausse." % inf)
    pr = ["je", "tu", "il/elle", "nous", "vous", "ils/elles"]
    lignes = "\n".join("· %s %s" % (pr[i], formes[i]) for i in range(6))
    return "Conjugaison de « %s » au présent de l'indicatif :\n%s" % (inf, lignes)


def _cap_graphique(texte: str):
    """« trace un graphique / une courbe de : n1, n2, … » -> SVG (rendu inline comme un schéma). Léger."""
    if not re.search(r"\b(trace|graphique|diagramme|courbe|barres?|histogramme)\b", texte, re.I):
        return None
    nums = re.findall(r"-?\d+(?:[.,]\d+)?", texte)
    vals = [float(n.replace(",", ".")) for n in nums]
    if len(vals) < 2:
        return None
    try:
        import graphique as _GR
        if re.search(r"\bcourbe\b", texte, re.I):
            d = _GR.courbe(list(range(1, len(vals) + 1)), vals)
        else:
            d = _GR.barres(vals)
        return _GR.vers_svg(d)
    except Exception:
        return None


def _cap_distance(texte: str):
    """« distance entre X et Y » -> orthodromie + cap (ia.distance_lieux/cap_lieux). Lourd (coordonnées)."""
    m = re.search(r"\b(?:distance|[ée]loign\w*)\b[^0-9]*?\b(?:entre|de|du|d['’])\s+(.+?)\s+"
                  r"(?:et|à|a|jusqu['’]?[àa]?)\s+(.+?)\s*\??\s*$", texte, re.I)
    _ia, _ = _charge_ia()
    if not _ia:
        return None
    if m:
        a, b = m.group(1).strip(" ?.\"'«»"), m.group(2).strip(" ?.\"'«»")
    else:
        # forme NUE « distance toulouse albi » (vécu test Yohan 2026-07-08) : on essaie les découpes
        # possibles — la paire n'est retenue QUE si les DEUX lieux résolvent en coordonnées (validation
        # par le lookup réel, jamais une découpe devinée).
        mn = re.search(r"\b(?:distance|[ée]loign\w*)\s+([\wà-ÿ' -]{3,60})\s*\??\s*$", texte, re.I)
        if not mn:
            return None
        mots = mn.group(1).strip(" ?.\"'«»").split()
        if not 2 <= len(mots) <= 6:
            return None
        a = b = None
        for i in range(1, len(mots)):
            ca, cb = " ".join(mots[:i]), " ".join(mots[i:])
            try:
                if _ia.distance_lieux(ca, cb) is not None:
                    a, b = ca, cb
                    break
            except Exception:
                continue
        if a is None:
            return None
    try:
        d = _ia.distance_lieux(a, b)
    except Exception:
        d = None
    if d is None:
        return None                                       # un lieu inconnu -> laisse le pipeline continuer (honnête)
    s = "La distance entre %s et %s est d'environ %s km (orthodromie, modèle sphérique)." % (
        a, b, format(round(d), ",d").replace(",", " "))
    try:
        cap = _ia.cap_lieux(a, b)
        if cap is not None:
            s += " Cap initial : %d°." % round(cap)
    except Exception:
        pass
    return s


# Intention CRÉATIVE OUVERTE (« invente/crée quelque chose », « as-tu des idées », « qu'est-ce que je peux
# créer ») — vécu Yohan 2026-07-06 : ces demandes tombaient dans une correction orthographique fausse puis une
# recherche web du texte littéral (Reverso !). Provara ne FABRIQUE pas d'idées (ce serait inventer au sens
# péjoratif = violer FAUX=0) ; il redirige HONNÊTEMENT vers ce qu'il sait vraiment faire.
_CREER_RE = re.compile(
    r"\b(?:inventer|invente|inventes|cr[ée]er|cr[ée]e|cr[ée]es|imaginer|imagine|concevoir|con[çc]ois|"
    r"trouver\s+(?:une\s+id[ée]e|des\s+id[ée]es)|des\s+id[ée]es|une\s+id[ée]e|innover)\b", re.I)
_CREER_OUVERT_RE = re.compile(
    r"\b(?:quelque\s+chose|un\s+truc|un\s+produit|un\s+objet|un\s+service|un\s+concept|"
    r"que\s+(?:puis|peux)[- ]je|qu['e ]est[- ]ce\s+que\s+je\s+(?:peux|pourrais)|"
    r"as[- ]tu\s+des?\s+id[ée]es?|aurais[- ]tu\s+des?\s+id[ée]es?|"
    r"(?:donne|propose|sugg[èe]re)[- ]?(?:moi|nous)?\s+(?:une|des?)\s+id[ée]es?|id[ée]e\s+de\s+\w+|"
    r"aide[- ]moi\s+[àa]\s+(?:inventer|cr[ée]er|imaginer|trouver))\b", re.I)


def _cap_creer_ouvert(texte: str):
    """Demande CRÉATIVE OUVERTE (« invente quelque chose », « as-tu des idées de produit ? », « qu'est-ce que je
    peux créer ? ») -> réponse HONNÊTE : Provara ne sort pas d'idées du néant (ce serait fabriquer), mais il
    oriente vers sa vraie mécanique d'invention (reformuler un besoin CONCRET en leviers physiques) et son
    scanner de manques. Ne se déclenche PAS sur un besoin déjà concret « X sans Y » (laissé à `_cap_invention`)."""
    if re.search(r"\bsans\s+\w", texte, re.I) or re.search(r"\bque\s+manque[\s-]*t[\s-]*il\b", texte, re.I):
        return None                                       # besoin concret -> _cap_invention gère
    if not (_CREER_RE.search(texte) and _CREER_OUVERT_RE.search(texte)):
        return None
    return (
        "Je ne vais pas te sortir une idée du chapeau — inventer au hasard, ce serait bluffer, et je ne bluffe "
        "jamais (c'est ma règle : un fait vérifié, ou je le dis). Mais voici comment je t'aide VRAIMENT à "
        "inventer, sans rien fabriquer :\n"
        "• Donne-moi un BESOIN CONCRET, sous la forme « comment faire X sans Y » — ex. « comment rafraîchir une "
        "pièce sans climatiseur ? ». Je le décompose alors en OBJECTIF RÉEL et en leviers physiques à explorer "
        "(conduction, évaporation, rayonnement…), avec la limite physique en jeu.\n"
        "• Ou demande-moi « quelles relations/attributs manquent dans ce que je connais ? » : je scanne mon "
        "graphe de 72 M de faits et te montre des manques RÉELS, re-vérifiés — des pistes concrètes, jamais "
        "inventées.\n"
        "Quel besoin concret veux-tu attaquer ?")


# Verbes d'ACTE DE LANGAGE (carte fermée) : « comment DIRE bonjour sans accent » n'est pas un besoin physique
# à décomposer -> l'invention s'abstient et laisse la cascade répondre (pin du banc conservé).
_VERBES_LANGAGE = frozenset(
    "dire ecrire prononcer traduire epeler parler formuler nommer appeler orthographier rediger conjuguer "
    "accorder exprimer".split())


def _cap_invention(texte: str):
    """« comment [faire] X sans Y » / « que manque-t-il pour X » -> reformulation PHYSIQUE du besoin (moteur
    d'invention besoin.py, la vision produit). FAUX=0 : ne répond QUE pour un besoin du catalogue physique ;
    besoin inconnu -> None (le web/pipeline prend le relais). Léger."""
    besoin_txt, explicite = None, False
    m = re.search(r"\bque\s+manque[\s-]*t[\s-]*il\s+pour\s+(.+?)\s*\??\s*$", texte, re.I)
    if m:
        besoin_txt, explicite = m.group(1), True         # intention d'invention SANS ambiguïté
    if besoin_txt is None:
        # FORME DIRECTE (vécu Phase 2 2026-07-09 : « invente un dispositif pour refroidir une maison sans
        # électricité » n'était PAS reconnue -> l'étage de clarification amont répondait à côté du moteur) :
        # « invente/imagine/propose/conçois … pour X » = intention d'invention EXPLICITE, X = le besoin.
        m = re.search(r"\b(?:invente[sz]?|imagine[sz]?|propose[sz]?|con[çc]oi[st])\b.{0,50}?\bpour\s+(.+?)\s*\??\s*$",
                      texte, re.I)
        # OBJET LANGAGIER/SOCIAL (carte fermée) : « invente une excuse pour mon retard » n'est pas un besoin
        # PHYSIQUE à décomposer — la méthode thermodynamique y serait à côté ; la cascade sert mieux.
        if m and not re.search(r"\b(?:excuses?|blagues?|histoires?|mensonges?|slogans?|po[èe]mes?|chansons?|"
                               r"noms?|titres?|surnoms?|pr[ée]textes?)\b", texte, re.I):
            besoin_txt, explicite = m.group(1), True
    physique = False
    if besoin_txt is None:
        m = re.search(r"\bcomment\s+(?:faire\s+pour\s+|je\s+peux\s+|)(.+?)\s+sans\s+.+?\s*\??\s*$", texte, re.I)
        if m:
            besoin_txt = m.group(1)
            # « comment X sans Y » est un vrai besoin d'invention SAUF quand X est un acte de LANGAGE
            # (« comment dire bonjour sans accent » n'est pas de la physique — pin du banc). Carte fermée.
            _tete = _normalise(besoin_txt).split()[0] if besoin_txt.strip() else ""
            physique = _tete not in _VERBES_LANGAGE
    if besoin_txt is None:
        return None
    besoin_txt = besoin_txt.strip(" ?.\"'«»")
    try:
        import besoin as _BSN
        d = _BSN.decompose(besoin_txt)
    except Exception:
        return None
    if not isinstance(d, dict) or d.get("statut") != "decompose":
        # HORS CATALOGUE physique. Intention d'invention CLAIRE (« que manque-t-il pour X », ou « comment X sans
        # Y » avec un X non-langagier) -> on AMPLIFIE (§13 : donner la MÉTHODE) au lieu de laisser filer vers
        # « internet coupé » (vécu audit 2026-07-08). Sinon (X = acte de langage) -> None, la cascade sert mieux.
        if not (explicite or physique):
            return None
        return ("« %s » : ce besoin précis n'est pas encore dans mon catalogue de leviers physiques vérifiés "
                "(aujourd'hui je décompose finement « rafraîchir une pièce ») — et je ne bluffe pas une physique "
                "que je n'ai pas. Voici comment on avance quand même, à MA façon :\n"
                "· CHIFFRE l'objectif réel (quelle quantité d'énergie, sur quelle durée, dans quel volume ?) — "
                "un besoin chiffré se décompose en canaux physiques, un slogan non.\n"
                "· Identifie le CANAL dominant (conduction, convection, rayonnement, évaporation, changement "
                "d'état) et le PUITS gratuit disponible (air nocturne, sol, eau du réseau, ciel).\n"
                "· La limite dure reste Carnot/la thermodynamique : le vrai gain vient de RÉDUIRE la charge et de "
                "viser un puits déjà favorable, jamais d'un rendement « magique »." % besoin_txt[:80])
    lignes = ["Regardons le BESOIN, pas la solution habituelle.", "", d.get("objectif_reel", "")]
    canaux = d.get("canaux") or []
    if canaux:
        lignes.append("")
        lignes.append("Leviers physiques à explorer :")
        for c in canaux[:5]:
            levier = getattr(c, "levier", None) or (c.get("levier") if isinstance(c, dict) else None)
            canal = getattr(c, "canal", None) or (c.get("canal") if isinstance(c, dict) else None)
            if levier:
                lignes.append("· %s%s" % ((canal + " : ") if canal else "", levier))
    if d.get("loi"):
        lignes.append("")
        lignes.append("Limite physique : " + str(d["loi"]))
    return "\n".join(x for x in lignes if x is not None).strip()


_LANG_INDICES = [("python", re.compile(r"\b(import |def |print\(|elif |lambda |self\.)", re.I)),
                 ("javascript", re.compile(r"\b(function |const |let |=>|console\.log|require\()", re.I)),
                 ("c", re.compile(r"#include|\bprintf\(|\bint main\b|\bmalloc\(", re.I)),
                 ("php", re.compile(r"<\?php|\$\w+\s*=|echo\s", re.I)),
                 ("sql", re.compile(r"\b(SELECT|INSERT|UPDATE|DELETE)\b.+\b(FROM|INTO|SET|WHERE)\b", re.I))]


def _cap_langue(texte: str, lang: str = None):
    """Question factuelle dans une langue étrangère supportée (en/es/de/it/pt) -> réponse DANS cette langue via
    le pipeline vérifié FR. None si non reconnue. Lourd (lecteur) : mode plein."""
    _ia, _ = _charge_ia()
    if not _ia:
        return None

    def _resolveur(requete_fr):
        try:
            r = _ia.donnee_nl(requete_fr)
            if r and r[0] == "verifie":
                return getattr(r[1], "valeur", None)
        except Exception:
            return None
        return None
    try:
        import langue
        return langue.repond_langue(texte, _resolveur, lang=lang)
    except Exception:
        return None


_ONTO_ESTUN_RE = re.compile(
    r"\b([a-zà-ÿ][\wà-ÿ'’\-]{2,})\s+est[- ](?:il|elle|ce)\s+(?:un|une|des|le|la|l['’]|un[e]?\s+sorte\s+de)\s+"
    r"([a-zà-ÿ][\wà-ÿ'’\-]{2,})\b", re.I)
_ONTO_ESTUN2_RE = re.compile(
    r"\best[- ]ce\s+qu['’e]?\s*(?:un |une |le |la |l['’])?([a-zà-ÿ][\wà-ÿ'’\-]{2,})\s+est\s+"
    r"(?:un|une|le|la|l['’])\s+([a-zà-ÿ][\wà-ÿ'’\-]{2,})\b", re.I)
_ONTO_COMMUN_RE = re.compile(
    r"(?:en\s+commun|point\s+commun\s+(?:entre|de|des))\b.*?\b([a-zà-ÿ][\wà-ÿ'’\-]{2,})\s+et\s+"
    r"(?:le\s+|la\s+|les\s+|l['’]|un\s+|une\s+)?([a-zà-ÿ][\wà-ÿ'’\-]{2,})\b", re.I)


# POINT COMMUN sur N ENTITÉS (≥2) : « qu'ont en commun le chat, le chien et le lion ? » -> intersection des chaînes
# is-a, plus proche ancêtre COMMUN à TOUTES. Corrige le 2-entités qui ignorait la 3e (regex « X et Y » seul). FAUX=0.
_COMMUN_LISTE_RE = re.compile(
    r"(?:qu[e'’]?\s*ont[- ]ils?\s+en\s+commun|qu[e'’]?\s*ont\s+en\s+commun|"
    r"(?:quel\s+est\s+(?:le\s+|leur\s+)?)?point\s+commun\s+(?:entre|de|des|à))\s+(.+?)\s*\??\s*$", re.I)


def _cap_point_commun_nway(texte: str):
    """PLUS PROCHE ANCÊTRE COMMUN à une LISTE d'entités (« qu'ont en commun le chat, le chien et le lion ? » ->
    mammifère). Intersection des chaînes is-a, vérifiée sur TOUTES les entités (pas seulement deux). FAUX=0 :
    ancêtre réel commun à tous, sinon None ; s'abstient si < 2 entités couvertes."""
    m = _COMMUN_LISTE_RE.search(texte)
    if not m:
        return None
    try:
        import est_un as _E
    except Exception:
        return None
    ents = [_strip_article(e.strip()) for e in re.split(r"\s*,\s*|\s+et\s+|\s+ou\s+", m.group(1)) if e.strip()]
    ents = [e for e in ents if e and len(e) >= 2]
    if len(ents) < 2:
        return None
    # chaîne is-a (ancêtres, du plus proche au plus lointain) de chaque entité ; on ne garde que celles couvertes
    chaines = [(e, [_E._norm(e)] + _E.chaine_isa(e)) for e in ents]
    couvertes = [(e, ch) for (e, ch) in chaines if len(ch) > 1]
    if len(couvertes) < 2:
        return None
    ref_e, ref_ch = couvertes[0]
    autres = [set(ch) for (_e, ch) in couvertes[1:]]
    commun = next((a for a in ref_ch[1:] if all(a in s for s in autres)), None)
    if not commun:
        return None
    manquants = len(ents) - len(couvertes)
    note = "" if manquants == 0 else " (%d non couvert%s)" % (manquants, "s" if manquants > 1 else "")
    quantif = "les deux" if len(couvertes) == 2 else "tous les %d" % len(couvertes)
    return "Leur point commun : %s (%s en sont une sorte)%s." % (_E.affiche(commun), quantif, note)


# FRUITS BOTANIQUES à usage CULINAIRE de légume : la question-piège classique (« la tomate est-elle un fruit
# ou un légume ? ») n'a pas UNE réponse — les deux points de vue sont vrais et on les DIT (jamais de « non » sec
# sur une vérité botanique). Liste fermée incontestable.
_DUAL_FRUIT_LEGUME = frozenset("tomate avocat concombre courgette aubergine poivron potiron citrouille".split())
_DUAL_FL_RE = re.compile(
    r"^\s*(?:est[- ]ce\s+que\s+)?(?:la\s+|le\s+|l['’ ]\s*|une?\s+)?([a-zà-ÿ]{3,})\s+"
    r"(?:est|c['’]est)[- ]?(?:elle|il)?\s+(?:bien\s+)?(?:un|une)\s+(fruit|l[ée]gume)", re.I)


def _cap_ontologie(texte: str):
    """RAISONNEMENT is-a conversationnel (« un chat est-il un mammifère ? » -> « Oui, … »; « qu'ont en commun le
    chat et le requin ? » -> « animal »), depuis la source SAINE `est_un` (classe_* curées + genre des définitions).
    FAUX=0 : « Oui » seulement si dérivable ; jamais de « Non » affirmé (monde ouvert) — on énonce plutôt le vrai
    genre connu. Le réseau de foule (JeuxDeMots) N'est PAS utilisé ici (trop bruité pour une assertion)."""
    md = _DUAL_FL_RE.match(texte.strip())
    if md and _normalise(md.group(1)) in _DUAL_FRUIT_LEGUME:
        n = md.group(1).lower()
        fem = n in ("tomate", "courgette", "aubergine", "citrouille")
        gn = ("l'" + n) if n[0] in "aàâeéèêiîouh" else (("la " if fem else "le ") + n)
        pron = "on la classe" if fem else "on le classe"
        return ("Les deux points de vue sont vrais pour %s : BOTANIQUEMENT c'est un FRUIT (issu de la fleur, "
                "il porte les graines) ; en CUISINE %s parmi les LÉGUMES. La réponse dépend de la convention — "
                "je ne tranche pas l'une contre l'autre." % (gn, pron))
    try:
        import est_un as _E
    except Exception:
        return None
    m = _ONTO_ESTUN_RE.search(texte) or _ONTO_ESTUN2_RE.search(texte)
    if m:
        # _strip_article : l'article ÉLIDÉ (« l'argent ») est collé au mot par le regex -> on le retire pour que
        # le lookup is-a trouve « argent » (sinon « l argent » ≠ « argent » et « l'argent est-il un métal » ratait).
        x, y = _strip_article(m.group(1).strip()), _strip_article(m.group(2).strip())
        if _normalise(x) == _normalise(y):
            return None
        # GARDE RELATIONNEL : « Berlin est-elle la capitale DE l'Allemagne ? » n'est PAS un is-a (« Berlin est-il
        # un <capitale> »), c'est un FAIT relationnel -> on laisse _oui_non/_connaissance trancher (sinon le genre
        # bruité de definition_nom « berlin = paquet » produisait une réponse absurde à une question VRAIE).
        if re.search(r"\b" + re.escape(y) + r"\s+(?:de\s+la|de\s+l['’]|du|des|de|d['’])\b", texte, re.I):
            return None
        # GARDE PROPRIÉTÉ DE MOT (vécu 2026-07-08) : « radar est-il un PALINDROME » interroge le MOT, pas
        # l'objet (« Le radar est un système — je ne le rattache pas… » répondait à côté). Famille fermée
        # de propriétés lexicales -> _cap_texte tranche nativement.
        if _normalise(y) in ("palindrome", "anagramme", "pangramme"):
            return None
        if _E.est_un(x, y):
            chaine = _E.chaine_isa(x)
            ny = _normalise(y)
            chemin = [x]
            for h in chaine:
                chemin.append(_E.affiche(h))
                if _normalise(h) == ny:
                    break
            return "Oui — %s." % " → ".join(chemin) if len(chemin) >= 2 else "Oui."
        genre = _E.chaine_isa(x)
        if genre:                       # x est couvert : on énonce ce qu'on SAIT plutôt qu'un « Non » (monde ouvert)
            try:
                import realisation_fr as _RF
                sujet, attr = _RF.le_nom(x, majuscule=True), _RF.un_nom(_E.affiche(genre[0]))
            except Exception:
                sujet, attr = x.capitalize(), _E.affiche(genre[0])
            return "%s est %s — je ne le rattache pas à « %s »." % (sujet, attr, y)
        return None
    m = _ONTO_COMMUN_RE.search(texte)
    if m:
        x, y = _strip_article(m.group(1).strip()), _strip_article(m.group(2).strip())
        commun = _E.genre_commun(x, y)
        if commun:
            return "Leur point commun : %s (les deux en sont une sorte)." % _E.affiche(commun)
        return None
    return None


_DEF_RE = re.compile(
    r"^\s*(?:qu['’ ]?est[- ]ce\s+qu['’e]?\s*(?:un\s|une\s|le\s|la\s|l['’])?\s*"
    r"|c['’ ]?est\s+quoi\s+(?:un\s|une\s|le\s|la\s|l['’])?\s*"
    # « quelle est la définition de X » / « quelle est la signification de X » (formes longues courantes) —
    # sans elles, la requête tombait dans la cascade LOURDE (chargement moteur ~100 s) au lieu de la voie légère.
    r"|quel(?:le)?\s+est\s+(?:la\s+|le\s+)?(?:d[ée]finition|signification)\s+d[eu'’]\s*"
    r"(?:un\s|une\s|le\s|la\s|l['’])?\s*"
    r"|d[ée]finition\s+d[eu'’]\s*(?:un\s|une\s|le\s|la\s|l['’])?\s*"
    r"|d[ée]finis[- ]?(?:moi\s+)?(?:un\s|une\s|le\s|la\s|l['’])?\s*"
    r"|qu['’ ]?entend[- ]on\s+par\s+(?:un\s|une\s|le\s|la\s|l['’])?\s*"
    r"|que\s+signifie\s+(?:un\s|une\s|le\s|la\s|l['’])?\s*"
    r"|qu['’ ]?est[- ]ce\s+qu['’e]?\s*)"
    r"[«\"']?\s*([\wà-ÿ][\wà-ÿ'’\- ]*?)\s*[»\"']?\s*\??\s*$", re.I)   # mot éventuellement CITÉ (« sérendipité »)
_DEF_RELS_CACHE = None


def _relations_definition() -> list:
    """Relations de DÉFINITION de la base (definition_*), `definition_nom` en tête (couverture générale)."""
    global _DEF_RELS_CACHE
    if _DEF_RELS_CACHE is None:
        try:
            rels = [f[:-6] for f in os.listdir(_DOSSIER_LECTEUR)
                    if f.endswith(".jsonl") and f.startswith("definition_")]
        except OSError:
            rels = []
        _DEF_RELS_CACHE = (["definition_nom"] if "definition_nom" in rels else []) + \
                          [r for r in rels if r != "definition_nom"]
    return _DEF_RELS_CACHE


# ————— RECHERCHE INVERSE : « quel PAYS a pour capitale Madrid ? » / « de quel pays Tokyo est la capitale ? » —————
# On part d'une VALEUR (Madrid) et on remonte à l'ENTITÉ (Espagne) via l'index inverse d'une relation connue.
# TYPE (« pays », « ville »…) + nom de relation FR -> relation réelle. FAUX=0 : ne rend que des couples stockés ;
# multi-valué listé (« quels pays ont pour monnaie l'euro » -> tous) ; index > 64 Mo -> abstention (garde RAM).
_INV_RELATIONS = {
    "capitale": ("capitale",), "monnaie": ("monnaie",), "president": ("president_pays",),
    "langue": ("langue_officielle",), "hymne": ("hymne_national",), "continent": ("continent",),
    "gentile": ("gentile",), "point culminant": ("point_culminant",), "indicatif": ("indicatif_pays",),
}
# forme 1 : « quel(s) TYPE a/ont pour REL VALEUR ? » / « … a comme REL VALEUR ? »
_INV_A_POUR_RE = re.compile(
    r"^(?:quel(?:le|s|les)?)\s+(pays|ville|etat|nation|monnaie|langue|continent)\s+"
    r"(?:a|ont)\s+(?:pour|comme)\s+([a-zà-ÿ' ]+?)\s+(.+?)\s*\??\s*$", re.I)
# forme 2 : « de quel TYPE VALEUR est(-elle) (la/le) REL ? »
_INV_DE_QUEL_RE = re.compile(
    r"^de\s+quel(?:le|s|les)?\s+(pays|ville|etat|nation|continent)\s+(.+?)\s+"
    r"est(?:[- ](?:elle|il|ce))?\s+(?:la\s+|le\s+|l['’]\s*|un\s+|une\s+)?([a-zà-ÿ' ]+?)\s*\??\s*$", re.I)
# forme 3 : phrasé VERBAL (« quels pays parlent français ? », « dans quels pays parle-t-on allemand ? »,
# « quels pays utilisent l'euro ? »). Le VERBE désigne la relation ; VALEUR = ce qui suit.
# clés NORMALISÉES (le tiret devient espace via _normalise : « parle-t-on » -> « parle t on »).
_INV_VERBE_REL = {
    "parle": "langue_officielle", "parlent": "langue_officielle", "parle t on": "langue_officielle",
    "utilise": "monnaie", "utilisent": "monnaie", "emploie": "monnaie", "emploient": "monnaie",
    "utilise t on": "monnaie",
}
_INV_VERBE_RE = re.compile(
    r"^(?:dans\s+)?quel(?:le|s|les)?\s+(?:pays|nation|etat)s?\s+"
    r"(parlent|parle|parle-t-on|utilisent|utilise|utilise-t-on|emploient|emploie)\s+"
    r"(?:le\s+|la\s+|les\s+|l['’]\s*|du\s+|de\s+la\s+|des\s+)?([a-zà-ÿ' ]+?)\s*\??\s*$", re.I)


def _cap_inverse(texte: str):
    """RECHERCHE INVERSE d'une relation : de la VALEUR vers l'ENTITÉ. « quel pays a pour capitale Madrid ? » ->
    Espagne ; « de quel pays Tokyo est la capitale ? » -> Japon. FAUX=0 : couples réellement stockés, listés si
    plusieurs ; None si la relation/valeur est inconnue. Complète la voie DIRECTE (« capitale de l'Espagne »)."""
    rel_fr = valeur = None
    rels = None
    m = _INV_VERBE_RE.match(texte.strip())            # forme VERBALE d'abord (« quels pays parlent français »)
    if m:
        rel = _INV_VERBE_REL.get(_normalise(m.group(1)))
        if rel:
            rels, valeur = (rel,), m.group(2)
    if rels is None:
        m = _INV_A_POUR_RE.match(texte.strip())
        if m:
            rel_fr, valeur = _normalise(m.group(2)), m.group(3)
        else:
            m = _INV_DE_QUEL_RE.match(texte.strip())
            if m:
                rel_fr, valeur = _normalise(m.group(3)), m.group(2)
        if not rel_fr or not valeur:
            return None
        rels = _INV_RELATIONS.get(rel_fr) or _INV_RELATIONS.get(rel_fr.rstrip("s"))
    if not rels or not valeur:
        return None
    cible = _normalise(_strip_article(valeur.strip()))
    if not cible or len(cible) < 2:
        return None
    for rel in rels:
        cell = _charge_reverse(rel).get(cible)
        if cell and cell[1]:
            ents = cell[1]
            if len(ents) == 1:
                try:
                    import realisation_fr as _RF
                    return _RF.article_pays(ents[0], majuscule=True) + "."
                except Exception:
                    return ents[0] + "."
            tete = ", ".join(ents[:20])
            suite = " …" if len(ents) > 20 else ""
            return "%d réponses : %s%s." % (len(ents), tete, suite)
    return None


def _cap_definition(texte: str):
    """« C'est quoi X ? » / « qu'est-ce qu'un X ? » / « définition de X » -> définition VÉRIFIÉE de la base
    (definition_nom : 292k+ noms du Wiktionnaire, puis definition_* de domaine). FAUX=0 : texte réel ou None."""
    # GARDE CODE MORSE (vécu 2026-07-08) : « que signifie ... --- ... en morse » n'est pas une définition de
    # l'animal — des tokens points/traits dans la phrase = décodage (fonction_nl).
    if re.search(r"(?:^|\s)[.\-]{2,}(?:\s|$)", texte):
        return None
    m = _DEF_RE.match(texte)
    if not m:
        return None
    ent = _strip_article(m.group(1).strip().strip("«»\"' ").strip())   # « sérendipité » cité entre guillemets
    if not ent or len(ent) < 2 or len(ent.split()) > 5:
        return None
    try:
        import est_un as _E
        d = _E.definition(ent)
    except Exception:
        d = None
    if not d:                                    # repli : definition_* de domaine (lecture directe)
        ne = _normalise(ent)
        for rel in _relations_definition():
            cell = _charge_direct(rel).get(ne)
            if cell and cell[1]:
                d = cell[1]
                break
    if not d:
        return None
    d = str(d).strip()
    return "%s : %s" % (ent[:1].upper() + ent[1:], d[:1].lower() + d[1:] if d else d)


def _singulier_fr(mot: str) -> str:
    """Singulier d'un nom FR, y compris les pluriels IRRÉGULIERS en -aux : « métaux » -> « métal », « chevaux » ->
    « cheval », mais « châteaux » -> « château » (-eaux -> -eau). Sinon retire un -s/-x final. Mots courts inchangés."""
    if len(mot) <= 4:
        return mot
    if mot.endswith("eaux"):
        return mot[:-1]                                  # château(x), bateau(x) : -eaux -> -eau
    if mot.endswith("aux"):
        return mot[:-3] + "al"                           # métaux -> métal, journaux -> journal
    if mot.endswith(("s", "x")):
        return mot[:-1]
    return mot


_HYPO_RES = (
    re.compile(r"\b(?:exemples?|types?|sortes?|esp[eè]ces?|vari[ée]t[ée]s?)\s+d[e'’]\s*(?:la\s|le\s|les\s|l['’])?"
               r"(.+?)\s*\??\s*$", re.I),
    re.compile(r"^\s*(?:quels?|quelles?)\s+sont\s+les\s+(.+?)\s*\??\s*$", re.I),
    re.compile(r"\b(?:cite|citez|liste|listez|nomme|nommez|donne(?:[- ]moi)?|donnez[- ]moi)\b.*?"
               r"\b(?:des|les|quelques|plusieurs)\s+(.+?)\s*\??\s*$", re.I),
    # « quels ANIMAUX sont des félins ? » / « quelles fleurs sont des orchidées ? » : le TYPE générique
    # (animaux/plantes…) est ignoré, la vraie catégorie est l'attribut « des X » -> hyponymes de X.
    re.compile(r"^\s*(?:quels?|quelles?)\s+[\wà-ÿ]+\s+sont\s+(?:des|les)\s+(.+?)\s*\??\s*$", re.I),
)


def _cap_hyponymes(texte: str):
    """« Quels sont les félins ? » / « cite des mammifères » / « des exemples de poissons » -> liste d'hyponymes
    RÉELS de la catégorie (index inverse du graphe is-a). FAUX=0 : entités réelles ou None, jamais inventées."""
    cat = None
    for rx in _HYPO_RES:
        m = rx.search(texte)
        if m:
            cat = _strip_article(m.group(1).strip())
            break
    if cat:                                          # retire une queue interrogative (« … existe-t-il », « … y a-t-il »)
        cat = re.sub(r"\s+(?:existe[- ]?t[- ]?ils?|existent[- ]?ils?|y\s+a[- ]?t[- ]?il|il\s+y\s+a|"
                     r"y\s+en\s+a[- ]?t[- ]?il|connais[- ]?tu|peux[- ]?tu)\b.*$", "", cat, flags=re.I).strip()
    if not cat or len(cat) < 3 or len(cat.split()) > 3:
        return None
    try:
        import est_un as _E
    except Exception:
        return None
    sing = _singulier_fr(cat)
    hypos = _E.hyponymes(sing, limite=15) or _E.hyponymes(cat, limite=15)
    if not hypos or len(hypos) < 2:
        return None
    montre = ", ".join(_E.affiche(h) for h in hypos[:15])
    suffixe = " …" if len(hypos) >= 15 else ""
    return "Par exemple : %s%s." % (montre, suffixe)


_DERIV_CONT_VILLE_RE = re.compile(
    r"(?:sur|dans|de)\s+quel\s+continent\s+(?:se\s+(?:trouve|situe)|est(?:[- ]elle)?(?:\s+situ\w+)?|se\s+situe)\s+"
    r"(?:la\s+ville\s+d[eu'’]\s*)?(.+?)\s*\??\s*$", re.I)


_ORBITE_RE = re.compile(
    r"(?:est[- ]ce\s+qu[e'’]?\s*)?(.+?)\s+(?:orbite|gravite|tourne)(?:nt)?"
    r"(?:[\s-]*t[\s-]+(?:ils?|elles?|on))?\b[^?]*?"
    r"(?:autour\s+)?(?:de\s+la\s+|de\s+l['’]|du\s+|des\s+|de\s+|d['’])?([\wà-ÿ'’\-][\wà-ÿ'’\- ]*?)\s*\??\s*$", re.I)
_SYSTEME_RE = re.compile(
    r"(?:est[- ]ce\s+qu[e'’]?\s*)?(.+?)\s+(?:fait[- ](?:il|elle)\s+partie|fait\s+partie|est[- ](?:il|elle)|appartient|"
    r"est\s+dans)"
    r"[^?]*?syst[eè]me\s+(?:(solaire)|(?:de\s+(?:la\s+|l['’])?|d['’])?([\wà-ÿ'’\- ]+?))\s*\??\s*$", re.I)


# ————— VIE QUOTIDIENNE (météo/heure/date) : des questions de tous les jours, pas des lookups de base —————
# L'HEURE et la DATE sont des FAITS vérifiables (l'horloge de la machine) -> réponse exacte. La MÉTÉO exige
# des capteurs/une position qu'on n'a pas -> refus honnête et CHALEUREUX (pas l'aveu robotique générique).
_METEO_RE = re.compile(
    r"\b(?:quel\s+temps\s+(?:fait[- ]il|il\s+fait|aujourd)|il\s+fait\s+quel\s+temps|la\s+m[ée]t[ée]o|"
    r"va[- ]?t[- ]?il\s+(?:pleuvoir|neiger)|il\s+(?:pleut|neige|fait\s+beau|fait\s+froid|fait\s+chaud)\b.{0,15}\?|"
    # température LIVE (« quelle température fait-il à Toulouse aujourd'hui ? ») — le marqueur fait-il/
    # aujourd'hui/dehors/en ce moment distingue la météo de la PHYSIQUE factuelle (point d'ébullition…)
    r"quelle\s+temp[ée]rature\s+(?:fait[- ]il|y\s+a[- ]?t[- ]?il|dehors)|"
    r"combien\s+de\s+degr[ée]s\s+(?:fait[- ]il|y\s+a[- ]?t[- ]?il)?\s*(?:dehors|aujourd['’ ]?hui|en\s+ce\s+moment)|"
    r"temp[ée]rature\b[^?]{0,40}\b(?:aujourd['’ ]?hui|demain|dehors|en\s+ce\s+moment|maintenant|cette\s+semaine))", re.I)
_HEURE_RE = re.compile(r"\bquel(?:le)?\s+heure\b|\bl['’]heure\s+qu['’]il\s+est\b|\bil\s+est\s+quel(?:le)?\s+heure\b"
                       r"|\b(?:donne|dis)[\w-]*\s+(?:moi\s+)?l['’]heure\b", re.I)
_DATE_JOUR_RE = re.compile(
    r"\bquel\s+jour\s+(?:de\s+la\s+semaine\s+)?(?:sommes[- ]nous|on\s+est|est[- ]on)\b"
    r"|\bquelle\s+est\s+la\s+date(?:\s+(?:d['’]\s*)?aujourd['’\w]*|\s+du\s+jour|\s+de\s+ce\s+jour)?\s*\??\s*$"
    r"|\bla\s+date\s+d['’]\s*aujourd|\bon\s+est\s+quel\s+jour\s+aujourd"
    r"|\bquel\s+jour\s+(?:sommes[- ]nous|on\s+est)\b|\bon\s+est\s+quel\s+jour\b"
    r"|\bon\s+est\s+le\s+combien\b|\bnous\s+sommes\s+le\s+combien\b|\bc['’]est\s+quel\s+jour\s+aujourd", re.I)
_JOURS_FR = ("lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche")
_MOIS_FR = ("janvier", "février", "mars", "avril", "mai", "juin", "juillet",
            "août", "septembre", "octobre", "novembre", "décembre")


_CHALLENGE_RE = re.compile(
    r"\b(?:challenges?[- ]moi|d[ée]fie[- ]moi|teste[- ]moi|interroge[- ]moi|que\s+tu\s+me\s+challenges?|"
    r"que\s+tu\s+me\s+testes?|que\s+tu\s+me\s+d[ée]fies?|teste\s+mes\s+connaissances|"
    r"pose[- ]moi\s+(?:une|des)\s+questions?(?:\s+difficiles?|\s+dures?)?|fais[- ]moi\s+r[ée]viser|"
    r"quiz(?:z|ze)?[- ]?moi|un\s+petit\s+quiz)\b(?:.*?\bsur\s+(.+?))?\s*\??\s*$", re.I)


# QUIZ VÉRIFIÉ (mandat Yohan 2026-07-08 « que l'IA nous challenge ») : Provara POSE une vraie question tirée
# de sa base VÉRIFIÉE, retient la réponse attendue par conversation, et TRANCHE la réponse de l'utilisateur au
# tour suivant contre le fait réel. FAUX=0 parfait : la question vient d'un fait vérifié, la correction EST le
# fait vérifié. Relations de quiz par sujet (carte FERMÉE : réponse courte, non ambiguë).
_QUIZ: dict = {}          # conv_id -> {"entite", "valeur", "relation", "libelle"}
_QUIZ_RELATIONS = {
    "geographie": ("capitale", "Quelle est la capitale de « %s » ?"),
    "capitales": ("capitale", "Quelle est la capitale de « %s » ?"),
    "chimie": ("numero_atomique", "Quel est le numéro atomique de « %s » ?"),
    "": ("capitale", "Quelle est la capitale de « %s » ?"),
}


def _quiz_question(sujet: str, conv_id):
    """Tire UNE question de la base vérifiée pour `sujet` (ou None si pas de relation de quiz / pas d'état
    possible). La réponse attendue est mémorisée par conversation — le tour suivant sera JUGÉ contre elle."""
    if not conv_id:
        return None
    rel_lib = _QUIZ_RELATIONS.get(_normalise(sujet or "").replace("la ", "").strip() or "")
    if rel_lib is None:
        return None
    rel, libelle = rel_lib
    try:
        import random
        table = _charge_direct(rel)
        if not table:
            return None
        cle = random.choice(list(table.keys()))
        cell = _lookup_cell(rel, cle)
        ent, val = (cell[0], cell[1]) if cell else (cle, table.get(cle))
        if val in (None, ""):
            return None
    except Exception:
        return None
    _QUIZ[conv_id] = {"entite": str(ent), "valeur": str(val), "relation": rel, "libelle": libelle}
    return libelle % ent


def _quiz_verdict(conv_id, texte: str):
    """Réponse au quiz EN ATTENTE -> verdict tranché par le fait vérifié, ou None (pas de quiz / l'utilisateur
    est passé à autre chose -> l'état est consommé et le pipeline reprend). « stop »-like -> fin propre."""
    q = _QUIZ.pop(conv_id, None) if conv_id else None
    if not q or not isinstance(texte, str):
        return None
    tn = " ".join(_normalise(texte).split())
    if tn in ("stop", "arrete", "j arrete", "fin", "on arrete", "non merci", "laisse tomber"):
        return "Fin du défi — bien joué de t'être prêté au jeu. Redis « challenge-moi » quand tu veux !"
    # une NOUVELLE demande (question interrogative substantielle) n'est pas une réponse au quiz : on n'otage
    # jamais la conversation — l'état est simplement consommé et la demande traitée normalement.
    if _veut_reponse(texte) and len(tn.split()) > 3:
        return None
    # ÉGALITÉ DE JETONS ÉPURÉS, jamais une sous-chaîne (vécu 2026-07-09, violation FAUX=0 mesurée : le tirage
    # « capitale du Burkina Faso » jugeait ✔ « Ouagadougou-les-Bains » (sous-chaîne) ET « pas Paris » (le mot y
    # est). On retire un lexique BORNÉ de remplissage (« c'est … je crois ») des DEUX côtés puis on exige
    # l'égalité exacte des jetons restants : la négation (« pas ») et tout excédent (« …-les-Bains ») recalent.
    _FILLER = {"c", "est", "ce", "je", "crois", "pense", "dirais", "dirai", "reponse", "la", "le", "les",
               "l", "il", "me", "semble", "euh", "heu", "hum", "ben", "bah", "alors", "oui", "ca", "doit",
               "peut", "etre"}
    _epure = lambda s: [m for m in s.split() if m not in _FILLER]
    attendu = _normalise(q["valeur"]).strip()
    if attendu and _epure(tn) == _epure(attendu):
        return ("✔ Exact — %s (fait vérifié de ma base). Redis « challenge-moi » pour une autre question."
                % q["valeur"])
    return ("✘ Non — pour « %s », la réponse vérifiée est %s (tu as dit : « %s »). "
            "Redis « challenge-moi » pour une autre." % (q["entite"], q["valeur"], texte.strip()[:60]))


def _cap_code_prouve(texte: str):
    """« écris une fonction/du code/un script [python|bash|javascript|perl] qui X » -> code PROUVÉ : les moteurs
    de synthèse (invente_et_retiens / genere_langage) génèrent des candidats et le JUGE les EXÉCUTE contre les
    exemples fournis (« (2, 3) -> 5 », le dernier gardé en aveugle). Sans exemples -> demande ACTIONNABLE (la
    méthode expliquée), jamais du code récité non exécuté. FAUX=0 : tout code livré a été jugé.
    Vécu Phase 2 2026-07-09 : l'axe code entier (0/5) tombait au fallback — voire au LEXIQUE (« tours de
    hanoï » -> liste de mots) — alors que les moteurs sont prouvés au diagnostic ; la ROUTE manquait."""
    n = _normalise(texte)
    if not (re.search(r"\b(?:ecris|ecrit|code|programme|implemente|genere|fais)\b", n)
            and re.search(r"\b(?:fonction|script|code|programme|algorithme)\b", n)):
        return None
    mlang = re.search(r"\b(python|bash|shell|javascript|js|perl)\b", n)
    lang = {"js": "javascript", "shell": "bash"}.get(mlang.group(1), mlang.group(1)) if mlang else "python"
    import ast
    exemples = []
    for m in re.finditer(r"\(([^()]*)\)\s*(?:->|=>|→|devient|donne)\s*([-\w.\"'\[\]]+)", texte):
        try:
            exemples.append((ast.literal_eval("(%s,)" % m.group(1).rstrip(",")), ast.literal_eval(m.group(2))))
        except (ValueError, SyntaxError):
            continue
    if len(exemples) < 2:
        return ("Je code à MA façon : je génère des candidats et mon JUGE les exécute contre des exemples "
                "réels — donne-moi 2 ou 3 exemples entrée → sortie dans ta demande (ex. « (2, 3) -> 5 » ; le "
                "3ᵉ est gardé en aveugle) et je te livre du code PROUVÉ (python, bash, javascript ou perl), "
                "jamais du code récité.")
    held = [exemples[-1]] if len(exemples) >= 3 else []
    vis = exemples[:-1] if held else exemples
    try:
        if lang == "python":
            import ia as _I
            sig = "%s->%s" % (type(vis[0][0][0]).__name__, type(vis[0][1]).__name__)
            v = _I.invente_et_retiens("fonction_demandee", sig, vis, held)
            if v is not None and getattr(v, "par", None) and v.statut in ("invention", "existe_deja"):
                src_code = v.par if v.par.lstrip().startswith("def ") else "def f(x):\n    return %s" % v.par
                return ("Code PROUVÉ — mon juge l'a exécuté sur tes %d exemple(s)%s :\n```python\n%s\n```\n"
                        "(x = le tuple des arguments · statut : %s%s)"
                        % (len(vis), (" + %d en aveugle" % len(held)) if held else "", src_code,
                           "invention nouvelle" if v.statut == "invention" else "capacité déjà connue",
                           (" — proche de « %s »" % v.proche_de) if getattr(v, "proche_de", None) else ""))
        else:
            bins = [(a[0], a[1], att) for a, att in exemples if isinstance(a, tuple) and len(a) == 2]
            if len(bins) >= 2:
                import ia as _I
                r = _I.genere_langage("fonction_demandee", bins[:-1] if len(bins) >= 3 else bins, lang,
                                      [bins[-1]] if len(bins) >= 3 else None)
                if r.ok:
                    return ("Code PROUVÉ (%s) — exécuté et vérifié sur tes exemples%s :\n```%s\n%s\n```"
                            % (lang, " + held-out" if r.generalise else "", lang, r.code))
            else:
                return ("Pour du %s je sais prouver les fonctions à DEUX arguments scalaires — donne les "
                        "exemples sous la forme « (a, b) -> résultat » (ou demande-la en python)." % lang)
    except Exception:
        pass
    return ("Aucun de mes candidats n'a passé TES exemples — je m'abstiens plutôt que de livrer du code non "
            "prouvé. Ajoute un exemple, vérifie-les, ou reformule la spécification.")


def _cap_challenge(texte: str, conv_id=None):
    """« Challenge-moi sur X » : Provara CHALLENGE pour de vrai — il POSE une question tirée de sa base
    vérifiée (réponse attendue mémorisée, jugée au tour suivant contre le fait réel), ET accepte toujours le
    mode inverse (l'utilisateur AFFIRME, Provara tranche V/F/Indécidable avec preuve). Jamais un bluff :
    question ET correction sortent du vérifié. Demandé par Yohan (2026-07-06 mémo ! ; 2026-07-08 quiz actif)."""
    m = _CHALLENGE_RE.search(texte)
    if not m:
        return None
    sujet = _strip_article((m.group(1) or "").strip(" ?.!")) if m.group(1) else ""
    cible = (" sur « %s »" % sujet) if sujet else ""
    question = _quiz_question(sujet, conv_id)
    if question:
        return ("Défi accepté%s — ma question, tirée de ma base vérifiée : %s "
                "(Réponds et je tranche contre le fait réel — ou dis « stop ». Tu peux aussi m'AFFIRMER "
                "quelque chose : je le jugerai Vrai/Faux/Indécidable, preuve à l'appui.)" % (cible, question))
    amorce = ""
    if sujet:
        try:
            import est_un as _E
            d = _E.definition(sujet) or _E.definition(sujet.split()[-1])
            if d:
                amorce = " Pour poser le décor, un fait vérifié — %s : %s." % (sujet, d[:160].rstrip("."))
        except Exception:
            pass
    return ("Défi accepté%s — mais à MA façon, parce que je ne bluffe jamais : AFFIRME des choses, et je "
            "tranche chacune par Vrai, Faux ou Indécidable, preuve à l'appui. Ce que la réalité ne tranche "
            "pas, je te le dirai honnêtement.%s À toi : lance ta première affirmation." % (cible, amorce))


# Domaine/URL EXPLICITE dans le message (« regarde yohanfauck.fr ») : URL complète, ou domaine avec une liste
# FERMÉE de TLD courants (jamais « maj.py » ni un mot à point accidentel). Vécu 2026-07-06 : « peux-tu regarder
# le site yohanfauck.fr ? » tombait dans la clarification générique — web ON = toujours une réponse.
_SITE_RE = re.compile(
    r"\b(https?://[^\s»«\"']+"
    r"|(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+(?:fr|com|org|net|io|dev|app|eu|be|ch|ca|ai|info|me)\b"
    r"(?:/[^\s»«\"']*)?)", re.I)
_SITE_AVIS_RE = re.compile(r"\b(?:penses?|pensez|avis|impressions?|trouves?|trouvez|juges?)\b", re.I)


def _cap_site(texte: str):
    """L'utilisateur NOMME un site : on va le LIRE et on RAPPORTE (titre + passage prose, attribué). FAUX=0 :
    jamais un jugement subjectif — si on demande « ce que tu en penses », on le dit et on cite la page."""
    m = _SITE_RE.search(texte)
    if not m:
        return None
    cible = m.group(1).rstrip(".,;!?")
    if os.environ.get("IA_WEB") != "1":
        return ("Tu me demandes d'aller voir « %s », mais Internet est coupé. Active-le (bouton « 🌐 » du menu "
                "⚙️) et j'irai lire la page pour t'en faire un rapport sourcé." % cible)
    try:
        import veille_structure as _VS
        ap = _VS.apercu_site(cible)
    except Exception:
        ap = None
    if not ap:
        return ("Je n'ai pas réussi à lire « %s » (site injoignable, vide, ou qui bloque les robots) — je "
                "préfère te le dire que d'inventer." % cible)
    titre, extrait, url = ap
    dom = url.split("//", 1)[-1].split("/")[0]
    lignes = []
    if _SITE_AVIS_RE.search(texte):
        lignes.append("Je ne porte pas de jugement subjectif — mais je suis allé LIRE la page, et voilà ce "
                      "qu'elle dit :")
    else:
        lignes.append("Je suis allé lire la page :")
    lignes.append("D'après %s%s : %s" % (dom, (" (« %s »)" % titre) if titre else "", extrait))
    lignes += ["", "\U0001F517 La page : %s" % url,
               "(Contenu rapporté tel quel — trouvé sur internet, à vérifier au besoin.)"]
    return "\n".join(lignes)


# ————— « MON AVIS » COMPARATIF : réflexion OUTILLÉE, pas ressentie (demande Yohan 2026-07-06) —————
# Un avis compatible FAUX=0 = une CONCLUSION SIGNÉE, dérivée de faits vérifiés, avec la règle de décision
# AFFICHÉE et la SENSIBILITÉ donnée (ce qui ferait basculer l'avis). Là où un humain « sent », Provara PÈSE :
# dominance de Pareto (aucune pondération ne peut inverser) sinon vote majoritaire des critères mesurés.
_AVIS_ENTRE_RE = re.compile(
    r"(?:meilleur\w*|mieux|pr[ée]f[ée]r\w*|choisir\w*|choix|recommand\w*|conseill\w*|avis|penses?[- ]tu)"
    r"[^?]*?\bentre\s+(.+?)\s+et\s+(.+?)\s*\??\s*$", re.I)
_AVIS_OU_RE = re.compile(
    r"(?:tu\s+)?(?:pr[ée]f[èe]res?|choisi(?:s|rais)|prendrais|recommandes?|conseilles?)\s+(?:plut[oô]t\s+)?"
    r"(.+?)\s+ou\s+(.+?)\s*\??\s*$", re.I)
# Relations chiffrées scannées pour une PAIRE (celles qui n'existent pas dans la base sont juste sautées).
_AVIS_RELS = ("superficie", "superficie_pays", "population_pays", "pib_pays", "pib_par_habitant_pays",
              "population_ville", "altitude_ville", "altitude_montagne", "altitude_sommet", "longueur_fleuve",
              "longueur_cours_eau", "hauteur_tour", "hauteur_gratte_ciel", "superficie_ile")
_AVIS_SUFFIXES = ("_pays", "_ville", "_montagne", "_sommet", "_col", "_fleuve", "_cours_eau", "_pont",
                  "_ligne_ferroviaire", "_ile", "_tour", "_gratte_ciel")


def _libelle_attr(rel: str) -> str:
    lib = rel
    for s in _AVIS_SUFFIXES:
        if lib.endswith(s):
            lib = lib[: -len(s)]
            break
    return lib.replace("_", " ").replace("pib", "PIB")


def _fmt_val(v, unite: str) -> str:
    t = format(int(v), ",d").replace(",", " ") if float(v).is_integer() else ("%g" % v)
    return (t + " " + unite).strip()


# L'avis RETIENT ses critères par conversation : le tour suivant qui en NOMME un re-tranche (« donne-moi ton
# critère n°1 » n'est plus une impasse — même principe que l'attente à trou météo, vécu 2026-07-06).
_AVIS_ATTENTE: dict = {}
_AVIS_CRITERE_RE = re.compile(r"\bcrit[èe]re\b|\bplut[oô]t\b", re.I)


def _cap_avis_critere(texte: str, conv_id=None):
    """Réponse au « donne-moi ton critère n°1 » d'un avis : « la population » / « mon critère est le PIB » ->
    re-tranche SUR CE critère (valeurs montrées). Critère inconnu nommé explicitement -> aveu honnête + liste
    des critères mesurables. Message sans rapport -> None (pipeline normal, l'état reste disponible)."""
    st = _AVIS_ATTENTE.get(conv_id) if conv_id else None
    if not st:
        return None
    tn = _normalise(texte)
    explicite = bool(_AVIS_CRITERE_RE.search(texte))
    if not explicite and len(tn.split()) > 6:
        return None
    # le libellé le PLUS LONG qui matche gagne (« PIB par habitant » ne doit pas retomber sur « PIB »)
    choisi = max((c for c in st["crits"] if _normalise(c[1]) in tn), key=lambda c: len(c[1]), default=None)
    if choisi is None:
        if not explicite:
            return None
        _AVIS_ATTENTE.pop(conv_id, None)
        qui = "/".join(st["noms"]) if st.get("multi") else "%s/%s" % (st["nx"], st["ny"])
        return ("Je n'ai pas de mesure VÉRIFIÉE de ce critère pour %s — je ne tranche jamais sur du non "
                "mesuré. Critères disponibles : %s. Nomme-en un et je conclus."
                % (qui, ", ".join(c[1] for c in st["crits"])))
    _AVIS_ATTENTE.pop(conv_id, None)
    if st.get("multi"):                                  # N candidats : classement complet sur CE critère
        rel, lib, vals = choisi
        u = _unite_attr(rel)
        ordonne = sorted(((n, v) for v, n in vals), key=lambda t: -t[1])
        return ("Avec TON critère (%s) : %s → mon avis suit ton critère : %s."
                % (lib, " > ".join("%s %s" % (n, _fmt_val(v, u)) for n, v in ordonne), ordonne[0][0]))
    rel, lib, vx, ax, vy, ay = choisi
    u = _unite_attr(rel)
    if vx == vy:
        return ("Sur TON critère (%s), %s et %s sont à égalité (%s) — ce critère ne peut pas trancher ; "
                "un autre ? (%s)" % (lib, ax, ay, _fmt_val(vx, u),
                                     ", ".join(c[1] for c in st["crits"] if c[1] != lib)))
    gagnant, vg, perdant, vp = (ax, vx, ay, vy) if vx > vy else (ay, vy, ax, vx)
    return ("Avec TON critère (%s) : %s %s devant %s %s → mon avis suit ton critère : %s."
            % (lib, gagnant, _fmt_val(vg, u), perdant, _fmt_val(vp, u), gagnant))


def _avis_multi(ents, conv_id=None):
    """AVIS à 3+ candidats : chaque critère mesuré est un ÉLECTEUR qui classe les candidats par valeur ;
    verdict par gagnant de CONDORCET (bat chacun en duel), repli BORDA si cycle (choix_social.py — le module
    de choix social enfin câblé au conversationnel). FAUX=0 : classements dérivés de faits vérifiés montrés."""
    crits, vus = [], set()
    for rel in _AVIS_RELS:
        vals = [_valeur_attr(e, rel) for e in ents]
        if any(v[0] is None for v in vals):
            continue
        lib = _libelle_attr(rel)
        if lib in vus:
            continue
        vus.add(lib)
        crits.append((rel, lib, vals))                   # vals[i] = (valeur, nom canonique) aligné sur ents
    if not crits:
        return None
    noms = [v[1] for v in crits[0][2]]
    lignes = ["Mon avis — CONSTRUIT, pas ressenti : chaque critère vérifié est un ÉLECTEUR qui classe les "
              "candidats, et je dépouille le scrutin (Condorcet)."]
    profil = []
    for rel, lib, vals in crits:
        u = _unite_attr(rel)
        ordonne = sorted(((n, v) for v, n in vals), key=lambda t: -t[1])
        profil.append(tuple(n for n, _v in ordonne))
        lignes.append("· %s : %s" % (lib, " > ".join("%s %s" % (n, _fmt_val(v, u)) for n, v in ordonne)))
    lignes.append("Ma convention (contestable, et c'est voulu) : « devant » = la plus grande valeur.")
    try:
        import choix_social as _CS
        gagnant = _CS.gagnant_condorcet(profil, noms)
        borda = None if gagnant else _CS.gagnant_borda(profil, noms)
    except Exception:
        gagnant = borda = None
    if gagnant:
        lignes.append("Mon avis : %s — gagnant de CONDORCET : il bat chacun des autres en duel, critère par "
                      "critère.%s" % (gagnant, " (Un seul critère mesurable : avis MINCE, je le signale.)"
                                      if len(crits) == 1 else ""))
    elif borda:
        lignes.append("Pas de gagnant de Condorcet (les critères se contredisent en cycle) — au compte de "
                      "BORDA, mon avis penche vers %s." % borda)
    else:
        lignes.append("Les critères ne départagent personne : je SUSPENDS mon avis — ton critère prioritaire "
                      "tranchera.")
    lignes.append("Donne-moi ton critère n°1 (%s) et je re-tranche en le suivant." % ", ".join(c[1] for c in crits))
    if conv_id:
        _AVIS_ATTENTE[conv_id] = {"multi": True, "crits": crits, "noms": noms}
    return "\n".join(lignes)


def _cap_avis(texte: str, conv_id=None):
    """« Quelle est la meilleure destination entre la France et l'Espagne ? » -> MON AVIS construit : chaque
    critère est un fait VÉRIFIÉ du lecteur (valeurs montrées), la règle est affichée, le verdict vient de
    pareto.domine (avis ROBUSTE) ou du vote des critères, et la sensibilité dit ce qui le ferait basculer.
    Rien de mesurable pour la paire -> None (le cadrage d'opinion existant reprend)."""
    m = _AVIS_ENTRE_RE.search(texte) or _AVIS_OU_RE.search(texte)
    if not m:
        return None
    # « entre X, Y et Z » -> 3+ candidats : vote de critères par CONDORCET/BORDA (choix_social.py, avis ④)
    ents = [_strip_article(e.strip(" ?.!«»\"'")) for e in re.split(r"\s*,\s*", m.group(1)) if e.strip()]
    ents.append(_strip_article(m.group(2).strip(" ?.!«»\"'")))
    ents = [e for e in ents if 0 < len(e) <= 40]
    if len(ents) != len({_normalise(e) for e in ents}) or len(ents) < 2:
        return None
    if len(ents) > 2:
        return _avis_multi(ents, conv_id)
    x, y = ents
    if not (0 < len(x) <= 40 and 0 < len(y) <= 40) or _normalise(x) == _normalise(y):
        return None
    crits, vus = [], set()
    for rel in _AVIS_RELS:
        vx, ax = _valeur_attr(x, rel)
        if vx is None:
            continue
        vy, ay = _valeur_attr(y, rel)
        if vy is None:
            continue
        lib = _libelle_attr(rel)
        if lib in vus:
            continue                                     # un seul critère par grandeur (pas de double comptage)
        vus.add(lib)
        crits.append((rel, lib, vx, ax, vy, ay))
    if not crits:
        return None
    nx, ny = crits[0][3], crits[0][5]
    if conv_id:                                          # le tour suivant peut nommer SON critère -> re-tranche
        _AVIS_ATTENTE[conv_id] = {"crits": crits, "nx": nx, "ny": ny}
    lignes = ["Mon avis — CONSTRUIT, pas ressenti : chaque critère est un fait vérifié, ma règle est affichée."]
    gx = gy = 0
    for rel, lib, vx, _ax, vy, _ay in crits:
        u = _unite_attr(rel)
        if vx > vy:
            gx += 1
            verdict = "devant : %s" % nx
        elif vy > vx:
            gy += 1
            verdict = "devant : %s" % ny
        else:
            verdict = "égalité"
        lignes.append("· %s : %s %s · %s %s → %s" % (lib, nx, _fmt_val(vx, u), ny, _fmt_val(vy, u), verdict))
    lignes.append("Ma convention (contestable, et c'est voulu) : « devant » = la plus grande valeur.")
    try:
        import pareto as _P
        sens = ("max",) * len(crits)
        a, b = tuple(c[2] for c in crits), tuple(c[4] for c in crits)
        dom_x, dom_y = _P.domine(a, b, sens), _P.domine(b, a, sens)
    except Exception:
        dom_x = dom_y = False
    if (dom_x or dom_y) and len(crits) == 1:
        lignes.append("Mon avis : %s — mais il ne tient qu'à UN critère mesurable (%s) : c'est un avis MINCE, "
                      "je le signale. Donne-moi tes critères (coût, climat, taille…) et je l'épaissis."
                      % (nx if dom_x else ny, crits[0][1]))
    elif dom_x or dom_y:
        lignes.append("Mon avis : %s — DOMINANCE DE PARETO sur %d critères : aucune pondération de ces "
                      "critères ne peut inverser ce verdict. Avis robuste." % (nx if dom_x else ny, len(crits)))
    elif gx != gy:
        if gx > gy:
            gagnant, contre = nx, [lib for _r, lib, vx, _a, vy, _b in crits if vy > vx]
        else:
            gagnant, contre = ny, [lib for _r, lib, vx, _a, vy, _b in crits if vx > vy]
        lignes.append("Mon avis : %s — en tête sur %d critère(s) sur %d au vote majoritaire."
                      % (gagnant, max(gx, gy), len(crits)))
        if contre:
            lignes.append("Sensibilité : mon avis BASCULE si ton critère prioritaire est %s — dis-le-moi et "
                          "je re-tranche." % " ou ".join(contre))
    else:
        lignes.append("Vote des critères : égalité %d–%d → je SUSPENDS mon avis (le trancheur, c'est TON "
                      "critère prioritaire — donne-le-moi et je conclus dans la seconde)." % (gx, gy))
    lignes.append("(Un « meilleur » absolu n'existe pas : cet avis vaut pour ces critères MESURABLES et il est "
                  "falsifiable — change la règle ou les critères, je recalcule.)")
    return "\n".join(lignes)


# DÉCISION QUOTIDIENNE SOUS INCERTITUDE (avis ⑤, §12 utilité espérée — 2026-07-07) : « dois-je prendre un
# parapluie ? ». La probabilité de pluie est RAPPORTÉE (Open-Meteo, structurée) ; les utilités sont une RÈGLE
# AFFICHÉE (se faire tremper coûte 10× le port) ; le verdict est CONDITIONNEL et re-tranchable — decision.py
# (utilité espérée + marge d'abstention) reçoit ici son premier consommateur conversationnel.
_PARAPLUIE_RE = re.compile(r"\b(parapluies?|k[- ]?way|imperm[ée]able|veste\s+de\s+pluie)\b", re.I)
_DECISION_PLUIE_RE = re.compile(r"\b(dois[- ]?je|faut[- ]?il|je\s+(?:prends|prenne)|prendre|besoin\s+d)\b", re.I)
# PONDÉRATION UTILISATEUR (marqueurs FERMÉS, sur texte normalisé) : « je re-tranche » n'est une promesse
# tenable que si la machine SAIT re-trancher — l'utilisateur règle le poids en le DISANT dans sa demande.
_PORT_PENIBLE_RE = re.compile(r"(pas envie de le (?:porter|trainer)|deteste (?:le )?porter|m encombre|encombrant)")
_CRAINT_PLUIE_RE = re.compile(r"(horreur d etre trempee?|horreur de la pluie|deteste etre trempee?|"
                              r"surtout pas (?:etre )?trempee?)")
# (libellé de règle, utilités) — la règle est TOUJOURS affichée : le verdict reste conditionnel et auditable.
_PONDERATIONS_PLUIE = {
    "defaut": ("se faire tremper coûte 10× le port du parapluie",
               {"prendre le parapluie": {"pluie": 1.0, "sec": -0.1}, "sortir sans": {"pluie": -1.0, "sec": 0.1}}),
    "port_penible": ("TA pondération : le port t'encombre (tremper ne coûte que 2× le port)",
                     {"prendre le parapluie": {"pluie": 1.0, "sec": -0.5},
                      "sortir sans": {"pluie": -1.0, "sec": 0.5}}),
    "craint_pluie": ("TA pondération : surtout ne pas être trempé (tremper coûte 20× le port)",
                     {"prendre le parapluie": {"pluie": 2.0, "sec": -0.1},
                      "sortir sans": {"pluie": -2.0, "sec": 0.1}}),
}
_MARGE_PLUIE = 0.05


def _ville_du_texte(texte: str) -> str:
    """Ville nommée dans une question météo/décision (« à Toulouse », « pour Brives ») — '' si absente."""
    mv = re.search(r"\b(?:[àa]|au|en|sur|pour)\s+((?:[A-ZÀ-Ü][\wà-ÿ'’-]+)(?:[\s-][A-ZÀ-Ü][\wà-ÿ'’-]+)*)"
                   r"|\b(?:[àa]|au)\s+([a-zà-ÿ][\wà-ÿ'’-]{2,})\b", texte)
    ville = (((mv.group(1) or mv.group(2)) if mv else "") or "").strip(" ?.!")
    return "" if _normalise(ville) in ("moment", "aujourd", "aujourd hui", "instant") else ville


def _conseil_parapluie(texte: str, conv_id=None):
    """Conseil CALCULÉ parapluie : probabilité de pluie rapportée × utilités affichées -> utilité espérée
    (decision.py), abstention honnête si l'écart est trop mince. Jamais un fait : un conseil conditionnel."""
    if os.environ.get("IA_WEB") != "1":
        return ("La pluie du jour est une donnée EN DIRECT : sans réseau, te conseiller serait deviner — et je "
                "ne devine jamais 🙂 Active Internet (bouton « 🌐 ») et je calcule le conseil sur la "
                "probabilité réelle.")
    ville = _ville_du_texte(texte)
    if not ville:
        try:
            import assistant_nl as _A
            _A.note_attente_slot(conv_id, "dois-je prendre un parapluie à %s ?")
        except Exception:
            pass
        return "Je peux calculer ça sur la probabilité de pluie réelle — pour quelle ville ?"
    try:
        import meteo as _MET
        rel = _MET.pluie_aujourdhui(ville)
    except Exception:
        rel = None
    if not rel:
        return ("Je n'ai pas réussi à obtenir la probabilité de pluie pour « %s » (ville inconnue du géocodeur "
                "ou réseau) — je préfère te le dire que d'inventer un conseil." % ville)
    import decision as _DEC
    tn = _normalise(texte)
    cle = ("port_penible" if _PORT_PENIBLE_RE.search(tn)
           else "craint_pluie" if _CRAINT_PLUIE_RE.search(tn) else "defaut")
    libelle_regle, utilites = _PONDERATIONS_PLUIE[cle]
    p = max(0.0, min(1.0, rel["proba_pluie"] / 100.0))
    st, action, eu = _DEC.decide({"pluie": p, "sec": 1.0 - p}, utilites, marge_abstention=_MARGE_PLUIE)
    ou = rel["nom"] + ((" (%s)" % rel["pays"]) if rel.get("pays") else "")
    tete = ("Conseil calculé — probabilité de pluie aujourd'hui à %s : %d %% (open-meteo.com — rapporté). "
            % (ou, rel["proba_pluie"]))
    regle = ("Règle affichée : %s. Pondération réglable — redis-le avec « pas envie de le porter » ou "
             "« horreur d'être trempé » et je re-tranche." % libelle_regle)
    if st == _DEC.ABSTENTION:
        return (tete + "Les deux options ont une utilité espérée trop proche pour trancher honnêtement — "
                "c'est un vrai pile ou face. " + regle)
    autre = next(a for a in eu if a != action)
    return (tete + "Mon conseil (utilité espérée %.2f contre %.2f) : %s. %s"
            % (eu[action], eu[autre], action, regle))


_MOIS_NUM = {"janvier": 1, "fevrier": 2, "février": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
             "juillet": 7, "aout": 8, "août": 8, "septembre": 9, "octobre": 10, "novembre": 11, "decembre": 12,
             "décembre": 12}
_DATE_FR_RE = re.compile(r"\b(1er|\d{1,2})\s+(janvier|f[ée]vrier|mars|avril|mai|juin|juillet|ao[ûu]t|septembre"
                         r"|octobre|novembre|d[ée]cembre)(?:\s+(\d{4}))?", re.I)


def _date_relative(texte: str):
    """« quel jour serons-nous dans 45 jours ? » / « quel jour était-on il y a 10 jours ? » — horloge de la
    machine + décalage calendaire EXACT (datetime, bissextiles comprises). Même statut que l'heure/la date
    locales déjà servies. FAUX=0 : « dans 3 mois » (durée ambiguë, 28-31 j) -> None, abstention."""
    t = texte.lower()
    m = re.search(r"\b(?:quel(?:le)?\s+(?:est\s+la\s+|sera\s+la\s+)?(?:jour|date)|on\s+sera)\b.{0,40}?"
                  r"\b(?:dans|d['’]ici)\s+(\d+)\s+(jours?|semaines?)\b", t)
    sens = 1
    if not m:
        m = re.search(r"\b(?:quel(?:le)?\s+(?:jour|date))\b.{0,40}?\bil\s+y\s+a\s+(\d+)\s+(jours?|semaines?)\b", t)
        sens = -1
    if not m:
        return None
    import datetime as _dt
    n = int(m.group(1)) * (7 if m.group(2).startswith("semaine") else 1)
    if n > 36600:                                     # ±100 ans : au-delà, la question n'est plus calendaire
        return None
    d = _dt.date.today() + _dt.timedelta(days=sens * n)
    verbe = "Nous serons le" if sens > 0 else "C'était le"
    return ("%s %s %d %s %d (décalage calendaire exact depuis l'horloge de ta machine)."
            % (verbe, _JOURS_FR[d.weekday()], d.day, _MOIS_FR[d.month - 1], d.year))


def _difference_dates(texte: str):
    """« combien de jours entre le 1er janvier et le 15 mars ? » -> 73 (calcul calendaire EXACT, datetime).
    Année absente -> année de l'horloge machine, ÉTIQUETÉE dans la réponse (une bissextile change le compte).
    FAUX=0 vécu : cette question servait « 31 » (les jours de janvier, gabarit lecteur trop large)."""
    t = texte.lower()
    if not re.search(r"\b(?:combien\s+de\s+jours|nombre\s+de\s+jours)\b", t):
        return None
    if not re.search(r"\bentre\b|\bdu\b.+?\bau\b", t):
        return None
    dates = _DATE_FR_RE.findall(texte)
    if len(dates) != 2:
        return None
    import datetime as _dt
    annee_defaut = _dt.date.today().year
    ds = []
    for jour, mois, annee in dates:
        j = 1 if jour.lower() == "1er" else int(jour)
        mo = _MOIS_NUM.get(mois.lower())
        try:
            ds.append((_dt.date(int(annee) if annee else annee_defaut, mo, j), bool(annee)))
        except (ValueError, TypeError):
            return None                               # 31 février… -> abstention, pas d'à-peu-près
    (d1, a1), (d2, a2) = ds
    if d2 < d1 and not (a1 or a2):                    # « entre le 15 mars et le 1er janvier » sans années :
        return None                                   # intention ambiguë (année suivante ?) -> abstention
    n = abs((d2 - d1).days)
    note = "" if (a1 and a2) else " — année %d prise sur l'horloge de ta machine (une bissextile change le compte)" % annee_defaut
    return ("%d jours entre le %d %s %d et le %d %s %d (calcul calendaire exact%s)."
            % (n, d1.day, _MOIS_FR[d1.month - 1], d1.year, d2.day, _MOIS_FR[d2.month - 1], d2.year, note))


# Grandes villes -> fuseau IANA (table FERMÉE, convention officielle tz ; clés normalisées sans accents).
# Hors table -> abstention honnête (jamais l'heure locale servie pour une ville étrangère, FAUX vécu).
_FUSEAUX_VILLES = {
    "paris": "Europe/Paris", "toulouse": "Europe/Paris", "lyon": "Europe/Paris", "marseille": "Europe/Paris",
    "bruxelles": "Europe/Brussels", "geneve": "Europe/Zurich", "londres": "Europe/London",
    "berlin": "Europe/Berlin", "madrid": "Europe/Madrid", "rome": "Europe/Rome", "lisbonne": "Europe/Lisbon",
    "moscou": "Europe/Moscow", "athenes": "Europe/Athens", "istanbul": "Europe/Istanbul",
    "new york": "America/New_York", "washington": "America/New_York", "montreal": "America/Toronto",
    "toronto": "America/Toronto", "chicago": "America/Chicago", "denver": "America/Denver",
    "los angeles": "America/Los_Angeles", "san francisco": "America/Los_Angeles",
    "mexico": "America/Mexico_City", "sao paulo": "America/Sao_Paulo", "buenos aires": "America/Argentina/Buenos_Aires",
    "rio de janeiro": "America/Sao_Paulo", "rio": "America/Sao_Paulo", "lima": "America/Lima",
    "bogota": "America/Bogota", "santiago": "America/Santiago", "la havane": "America/Havana",
    "le caire": "Africa/Cairo", "caire": "Africa/Cairo", "dakar": "Africa/Dakar", "abidjan": "Africa/Abidjan",
    "johannesburg": "Africa/Johannesburg", "casablanca": "Africa/Casablanca", "alger": "Africa/Algiers",
    "tunis": "Africa/Tunis", "kinshasa": "Africa/Kinshasa", "nairobi": "Africa/Nairobi",
    "dubai": "Asia/Dubai", "tokyo": "Asia/Tokyo", "pekin": "Asia/Shanghai", "shanghai": "Asia/Shanghai",
    "hong kong": "Asia/Hong_Kong", "singapour": "Asia/Singapore", "seoul": "Asia/Seoul",
    "bombay": "Asia/Kolkata", "mumbai": "Asia/Kolkata", "new delhi": "Asia/Kolkata", "delhi": "Asia/Kolkata",
    "bangkok": "Asia/Bangkok", "jakarta": "Asia/Jakarta", "sydney": "Australia/Sydney",
    "melbourne": "Australia/Melbourne", "auckland": "Pacific/Auckland", "papeete": "Pacific/Tahiti",
    "noumea": "Pacific/Noumea", "cayenne": "America/Cayenne", "fort-de-france": "America/Martinique",
    "pointe-a-pitre": "America/Guadeloupe", "saint-denis": "Indian/Reunion",
}


def _cap_quotidien(texte: str, conv_id=None):
    """Questions du QUOTIDIEN : météo (refus honnête, chaleureux), heure et date (faits réels de l'horloge
    locale), conseil parapluie CALCULÉ (probabilité rapportée × utilité espérée, decision.py). Demandé par
    Yohan (2026-07-06) : « il fait quel temps ? » tombait dans l'aveu générique."""
    if _PARAPLUIE_RE.search(texte) and _DECISION_PLUIE_RE.search(texte):
        return _conseil_parapluie(texte, conv_id)
    if _METEO_RE.search(texte):
        # WEB ON -> VRAIE météo (source STRUCTURÉE Open-Meteo, relevé attribué — exigence Yohan : « si
        # Internet est activé, il peut très bien aller vérifier »). WEB OFF -> refus honnête + geste.
        if os.environ.get("IA_WEB") == "1":
            ville = _ville_du_texte(texte)
            if not ville:
                try:      # ATTENTE À TROU : le tour suivant (« A Brives ») COMPLÈTE la question météo au lieu
                    import assistant_nl as _A                  # de repartir en recherche web (vécu 2026-07-06)
                    _A.note_attente_slot(conv_id, "quel temps fait-il à %s ?")
                except Exception:
                    pass
                return ("Je peux te donner la météo en direct — pour quelle ville ? (« quel temps fait-il à "
                        "Toulouse ? »)")
            try:
                import meteo as _MET
                rel = _MET.actuelle(ville)
            except Exception:
                rel = None
            if rel:
                morceaux = ["%g °C" % rel["temperature"]]
                if rel.get("libelle"):
                    morceaux.append(rel["libelle"])
                if rel.get("vent_kmh") is not None:
                    morceaux.append("vent %g km/h" % rel["vent_kmh"])
                ou = rel["nom"] + ((" (%s)" % rel["pays"]) if rel.get("pays") else "")
                quand = (" à %s" % rel["heure"]) if rel.get("heure") else ""
                return ("À %s en ce moment : %s (relevé open-meteo.com%s — rapporté, pas de ma base)."
                        % (ou, ", ".join(morceaux), quand))
            return ("Je n'ai pas réussi à obtenir le relevé météo pour « %s » (ville inconnue du géocodeur ou "
                    "réseau) — je préfère te le dire que d'inventer." % ville)
        return ("Internet est coupé, et la météo est une donnée EN DIRECT : sans réseau, te répondre serait "
                "deviner — et je ne devine jamais 🙂 Active Internet (bouton « 🌐 ») et je te donne le relevé "
                "réel, sourcé.")
    r = _date_relative(texte)
    if r:
        return r
    r = _difference_dates(texte)
    if r:
        return r
    # JOUR DE LA SEMAINE d'une date HISTORIQUE : « quel jour de la semaine était le 14 juillet 1789 ? » ->
    # mardi (datetime, calendrier grégorien proleptique — année EXPLICITE ≥ 1583 exigée : avant, le julien
    # s'appliquait -> abstention plutôt qu'un jour décalé).
    # FUTUR accepté (« quel jour tombera le 25 décembre » partait en fuzzy « 24 decembre » -> « 2019 », FAUX
    # vécu 2026-07-08) + date SANS année -> année de l'horloge, ÉTIQUETÉE ; verbe accordé (était/est/sera).
    mjs = (re.search(r"quel\s+jour\s+(?:de\s+la\s+semaine\s+)?(?:[ée]tait|est|sera|tombait|tombe(?:ra)?)\s+le\s+",
                     texte, re.I)
           or re.search(r"\ble\s+\d.{0,24}?\btombe(?:ra)?\s+quel\s+jour", texte, re.I))
    if mjs:
        md = _DATE_FR_RE.search(texte)
        if md:
            j = 1 if md.group(1).lower() == "1er" else int(md.group(1))
            mo = _MOIS_NUM.get(md.group(2).lower())
            import datetime as _dt
            annee_horloge = not md.group(3)
            an = int(md.group(3)) if md.group(3) else _dt.date.today().year
            if an >= 1583:
                try:
                    d = _dt.date(an, mo, j)
                except (ValueError, TypeError):
                    return None
                auj = _dt.date.today()
                verbe = "sera" if d > auj else ("était" if d < auj else "est")
                note = (" — année %d prise sur l'horloge de ta machine" % an) if annee_horloge else ""
                return ("Le %d %s %d %s un %s (calendrier grégorien%s)."
                        % (d.day, _MOIS_FR[d.month - 1], d.year, verbe, _JOURS_FR[d.weekday()], note))
            return ("Avant 1583, le calendrier julien s'appliquait (bascule grégorienne d'octobre 1582) — je "
                    "m'abstiens plutôt que de te donner un jour décalé.")
    if _HEURE_RE.search(texte):
        import time as _t
        # GARDE HEURE ÉNONCÉE (FAUX vécu 2026-07-08) : « un train part à 8h et roule 2 heures, à quelle
        # heure arrive-t-il » recevait l'heure ACTUELLE. Une heure DITE dans la question = un problème
        # d'arithmétique d'horloge (fonction_nl), jamais l'horloge machine.
        if re.search(r"(?:[àa]|il\s+est|de)\s+\d{1,2}\s*h\s*[0-5]?\d?\b(?!\s*/)", _normalise(texte)):
            return None
        # GARDE ÉPHÉMÉRIDES (FAUX vécu 2026-07-08) : « à quelle heure le soleil se couche » recevait l'heure
        # ACTUELLE. Lever/coucher = astronomie locale (lieu + date) — abstention honnête, pas l'horloge.
        if re.search(r"soleil|lune\b|aube|crepuscule|cr[ée]puscule", _normalise(texte)):
            return ("L'heure du lever/coucher dépend du lieu et du jour — je n'ai pas d'éphémérides vérifiées "
                    "sous la main, je préfère m'abstenir plutôt que te donner l'heure de l'horloge.")
        # HEURE FUTURE/PASSÉE : « quelle heure sera-t-il dans 3 heures » recevait l'heure ACTUELLE (FAUX
        # vécu). Décalage exact sur l'horloge machine, modulo 24 h.
        mfut = re.search(r"dans\s+(\d+)\s+(heures?|minutes?)\b", _normalise(texte))
        if mfut and re.search(r"sera|serait", _normalise(texte)):
            import datetime as _dt
            delta = _dt.timedelta(**{"hours" if mfut.group(2).startswith("heure") else "minutes":
                                     int(mfut.group(1))})
            fu = _dt.datetime.now() + delta
            return ("Il sera %02d h %02d (horloge de ta machine + %s %s)."
                    % (fu.hour, fu.minute, mfut.group(1), mfut.group(2)))
        # FAUX=0 vécu 2026-07-08 : « quelle heure est-il à New York ? » servait l'heure LOCALE de la machine.
        # Ville nommée -> fuseau IANA (table fermée de grandes villes + zoneinfo, base tz officielle) ;
        # ville APRÈS « à » mais hors table, ou base tz absente -> abstention honnête, JAMAIS l'heure locale.
        tn = " %s " % _normalise(texte)
        ville_conn = next((v for v in _FUSEAUX_VILLES
                           if " %s " % v in tn), None)          # la ville peut être N'IMPORTE OÙ (« tokyo il
        #                                                          est quelle heure » servait l'heure locale)
        if ville_conn:
            try:
                from zoneinfo import ZoneInfo
                import datetime as _dt
                lh = _dt.datetime.now(ZoneInfo(_FUSEAUX_VILLES[ville_conn]))
                if conv_id:                              # continuation « et à New York ? » (type B rejouable)
                    _DERNIER_SUJET[conv_id] = ville_conn
                    _DERNIER_QUESTION[conv_id] = "quelle heure est-il à %s ?" % ville_conn
                return ("À %s il est %02d h %02d (fuseau %s, base de fuseaux IANA + horloge de ta machine)."
                        % (ville_conn.title(), lh.hour, lh.minute, _FUSEAUX_VILLES[ville_conn]))
            except Exception:
                return ("Je n'ai pas la base de fuseaux horaires sous la main — je préfère m'abstenir plutôt "
                        "que te donner l'heure locale de TA machine comme si c'était celle de %s."
                        % ville_conn.title())
        # ⚠ la ville peut contenir des particules MINUSCULES (« Rio de Janeiro ») : l'ancien motif exigeait
        # chaque mot capitalisé -> l'ancre de fin ratait et l'heure LOCALE était servie (FAUX vécu 2026-07-08).
        # Capture permissive après la majuscule initiale : au pire on s'abstient avec un libellé large.
        mv = re.search(r"\b(?:a|à)\s+([A-ZÀ-Ÿ][\w'’ -]*?)\s*\??\s*$", texte.strip())
        if mv:
            return ("Je ne connais pas le fuseau horaire vérifié de « %s » — je préfère m'abstenir plutôt que "
                    "te donner l'heure locale de TA machine comme si c'était la sienne." % mv.group(1))
        lt = _t.localtime()
        return "Il est %02d h %02d (horloge de ta machine)." % (lt.tm_hour, lt.tm_min)
    # COMPTE À REBOURS vers une date de l'année : « dans combien de jours le 25 décembre / Noël » (année
    # courante ; si la date est passée, l'an prochain). Horloge machine + datetime, calcul calendaire exact.
    mcr = re.search(r"(?:dans\s+)?combien\s+de\s+jours\s+(?:jusqu['’à]*\s*(?:au|a|à)?\s*|avant\s+|reste[- ]t[- ]il"
                    r"\s+(?:avant|jusqu[e'’]*)\s*|il\s+reste\s+(?:avant|jusqu[e'’]*)\s*)?"
                    r"(?:le\s+)?(no[eë]l|(1er|\d{1,2})\s+(janvier|f[ée]vrier|mars|avril|mai|juin|juillet"
                    r"|ao[ûu]t|septembre|octobre|novembre|d[ée]cembre))", texte, re.I)
    if mcr:
        import datetime as _dt
        auj = _dt.date.today()
        if mcr.group(1) and _normalise(mcr.group(1)).startswith("noel"):
            j, mo = 25, 12
        else:
            j = 1 if (mcr.group(2) or "").lower() == "1er" else int(mcr.group(2))
            mo = _MOIS_NUM.get(_normalise(mcr.group(3)))
        if mo:
            try:
                cible = _dt.date(auj.year, mo, j)
                if cible < auj:
                    cible = _dt.date(auj.year + 1, mo, j)
                n = (cible - auj).days
                return ("%d jours (jusqu'au %d %s %d — calcul depuis l'horloge de ta machine)."
                        % (n, cible.day, _MOIS_FR[cible.month - 1], cible.year))
            except (ValueError, TypeError):
                return None
    # DATE COMPLÈTE de naissance -> âge EXACT (« né le 15 mars 1990 » ; tombait en repli, vécu 2026-07-08).
    mage_d = re.search(r"n[ée]e?\s+le\s+(1er|\d{1,2})\s+([a-zà-ÿ]+)\s+(\d{4})", texte, re.I)
    if mage_d and re.search(r"[âa]ge", texte, re.I):
        import datetime as _dt
        mo = _MOIS_NUM.get(mage_d.group(2).lower())
        if mo:
            try:
                naiss = _dt.date(int(mage_d.group(3)), mo,
                                 1 if mage_d.group(1).lower() == "1er" else int(mage_d.group(1)))
            except ValueError:
                return None
            auj = _dt.date.today()
            if naiss <= auj:
                age = auj.year - naiss.year - ((auj.month, auj.day) < (naiss.month, naiss.day))
                return ("%d ans (né(e) le %d %s %d, nous sommes le %02d/%02d/%d à l'horloge de ta machine)."
                        % (age, naiss.day, _MOIS_FR[naiss.month - 1], naiss.year, auj.day, auj.month, auj.year))
            return None
    # ANNÉE seule -> fourchette honnête ; phrasés élargis (« si je suis né en 1990 quel âge j'ai », vécu).
    mage = (re.search(r"quel\s+[âa]ge\s+a\s+(?:une\s+personne|quelqu['’]un)\s+n[ée]e?\s+en\s+(\d{4})",
                      texte, re.I)
            or re.search(r"n[ée]e?\s+en\s+(\d{4}).{0,20}?quel\s+[âa]ge", texte, re.I)
            or re.search(r"quel\s+[âa]ge\b.{0,25}?\bn[ée]e?\s+en\s+(\d{4})", texte, re.I))
    if mage:
        import datetime as _dt
        auj = _dt.date.today()
        an = int(mage.group(1))
        if an <= auj.year:
            a2 = auj.year - an
            return ("%d ou %d ans selon que l'anniversaire est passé (né(e) en %d, nous sommes le %02d/%02d/%d "
                    "à l'horloge de ta machine)." % (a2 - 1, a2, an, auj.day, auj.month, auj.year))
        return None
    # ANNÉE FUTURE / COMPTE D'ANNÉES : « quelle année dans 10 ans » -> 2036 ; « dans combien d'années 2050 »
    # -> 24 (l'un partait en « c'est subjectif », l'autre en repli — vécu 2026-07-08).
    tn2 = _normalise(texte)
    man2 = re.search(r"quelle\s+annee\s+(?:serons[- ]nous\s+|sera[- ]t[- ]on\s+)?dans\s+(\d+)\s+ans", tn2)
    if man2:
        import datetime as _dt
        y = _dt.date.today().year
        return "En %d (%d + %s, année de l'horloge de ta machine)." % (y + int(man2.group(1)), y, man2.group(1))
    man3 = re.search(r"dans\s+combien\s+d\s*annees?\s+(?:serons[- ]nous\s+en\s+)?(\d{4})\b", tn2)
    if man3:
        import datetime as _dt
        y, cible_a = _dt.date.today().year, int(man3.group(1))
        if cible_a > y:
            return "Dans %d ans (%d − %d, année de l'horloge de ta machine)." % (cible_a - y, cible_a, y)
        if cible_a == y:
            return "C'est cette année (%d à l'horloge de ta machine)." % y
        return "C'était il y a %d ans (%d − %d)." % (y - cible_a, y, cible_a)
    # CALENDRIER COURANT (horloge machine, tout ÉTIQUETÉ) — saison, semaine ISO, jour de l'année, jours
    # restants, bissextile relative (tombaient en repli/mémo, vécu 2026-07-08).
    if re.search(r"quelle\s+saison\s+(?:sommes[- ]nous|est[- ]on|est[- ]ce)|en\s+quelle\s+saison", tn2):
        import datetime as _dt
        auj = _dt.date.today()
        nom = "hiver"
        for borne, s in (((3, 20), "printemps"), ((6, 21), "été"), ((9, 22), "automne"), ((12, 21), "hiver")):
            if (auj.month, auj.day) >= borne:
                nom = s
        oppose = {"printemps": "automne", "été": "hiver", "automne": "printemps", "hiver": "été"}[nom]
        return ("%s dans l'hémisphère nord (%s dans le sud) — bornes astronomiques approximatives (±1 jour "
                "selon l'année) ; nous sommes le %02d/%02d à l'horloge de ta machine."
                % (nom.capitalize(), oppose, auj.day, auj.month))
    if re.search(r"num[e]ro\s+de\s+(?:la\s+)?semaine|quelle\s+semaine\s+(?:sommes[- ]nous|est[- ]on)", tn2):
        import datetime as _dt
        iso = _dt.date.today().isocalendar()
        return "Semaine %d de %d (numérotation ISO 8601, horloge de ta machine)." % (iso[1], iso[0])
    if re.search(r"jours?\b.{0,30}?\bfin\s+de\s+l\s*annee", tn2) and re.search(r"combien|reste|restant", tn2):
        import datetime as _dt
        auj = _dt.date.today()
        n = (_dt.date(auj.year, 12, 31) - auj).days
        return "%d jours jusqu'au 31 décembre %d (horloge de ta machine)." % (n, auj.year)
    mjo = re.search(r"(\d{1,3})\s*(?:e|eme)\b\s+jour\s+de\s+l\s*annee", tn2)
    if mjo:
        import datetime as _dt
        auj = _dt.date.today()
        n = int(mjo.group(1))
        nb = 366 if (auj.year % 4 == 0 and (auj.year % 100 != 0 or auj.year % 400 == 0)) else 365
        if 1 <= n <= nb:
            d = _dt.date(auj.year, 1, 1) + _dt.timedelta(days=n - 1)
            return ("Le %d %s (%de jour de %d — année de l'horloge de ta machine)."
                    % (d.day, _MOIS_FR[d.month - 1], n, auj.year))
        return "L'année %d n'a que %d jours — pas de %de jour." % (auj.year, nb, n)
    if re.search(r"quel\s+jour\s+de\s+l\s*annee\s+sommes[- ]nous|numero\s+du\s+jour\s+dans\s+l\s*annee", tn2):
        import datetime as _dt
        auj = _dt.date.today()
        return "Le %de jour de %d (horloge de ta machine)." % (auj.timetuple().tm_yday, auj.year)
    mbis = re.search(r"(?:l\s*)?annee\s+(prochaine|derniere)\b.{0,20}?bissextile"
                     r"|bissextile.{0,20}?annee\s+(prochaine|derniere)|cette\s+annee\b.{0,25}?bissextile", tn2)
    if mbis:
        import calendar as _cal
        import datetime as _dt
        y = _dt.date.today().year
        rel = mbis.group(1) or mbis.group(2)
        y2 = y + 1 if rel == "prochaine" else y - 1 if rel == "derniere" else y
        return ("%s — %d %s bissextile (règle grégorienne ; année calculée depuis l'horloge de ta machine)."
                % ("Oui" if _cal.isleap(y2) else "Non", y2, "est" if _cal.isleap(y2) else "n'est pas"))
    if _DATE_JOUR_RE.search(texte):
        import time as _t
        lt = _t.localtime()
        return ("Nous sommes le %s %d %s %d (horloge de ta machine)."
                % (_JOURS_FR[lt.tm_wday], lt.tm_mday, _MOIS_FR[lt.tm_mon - 1], lt.tm_year))
    return None


# GÉNÉRATION D'ANAGRAMMES : « anagramme de chien » -> niche, chine — mots RÉELS du dictionnaire embarqué
# (definition_nom, 292k noms du Wiktionnaire), jamais des lettres mélangées inventées. Comparaison sans
# accents (génie/neige), affichage de la forme du dictionnaire. Scan streaming unique, mémoïsé par clé triée.
_ANAG_GEN_RE = re.compile(
    r"^\s*(?:c['’]est\s+quoi\s+|quelle?\s+est\s+)?(?:donne[- ]moi\s+|trouve\s+|cherche\s+)?"
    r"(?:une?\s+|les?\s+|des\s+|l['’]\s*)?anagrammes?\s+"
    r"(?:du\s+mot\s+|de\s+|d['’]\s*)([a-zà-ÿA-ZÀ-Ÿ-]+)\s*\??\s*$", re.I)
_ANAG_MEMO: dict = {}


def _cap_anagramme(texte: str):
    m = _ANAG_GEN_RE.match(texte.strip())
    if not m:
        return None
    mot = m.group(1).lower()
    if not (3 <= len(mot) <= 14):
        return None
    nm = _normalise(mot)
    cle = "".join(sorted(nm))
    res = _ANAG_MEMO.get(cle)
    if res is None:
        res = []
        chemin = os.path.join(_DOSSIER_LECTEUR, "definition_nom.jsonl")
        try:
            with open(chemin, encoding="utf-8") as fh:
                for l in fh:
                    i = l.find('"entite": "')
                    if i < 0:
                        continue
                    j = l.find('"', i + 11)
                    ent = l[i + 11:j]
                    if " " in ent or "-" in ent or len(ent) > 16:
                        continue
                    ne = _normalise(ent)
                    if len(ne) == len(cle) and "".join(sorted(ne)) == cle and ent not in res:
                        res.append(ent)
                        if len(res) >= 9:
                            break
        except OSError:
            return None
        _ANAG_MEMO[cle] = res
    autres = [r for r in res if _normalise(r) != nm]
    if autres:
        return ("Anagramme(s) de « %s » dans mon dictionnaire (noms communs du Wiktionnaire) : %s."
                % (mot, ", ".join(autres[:8])))
    return ("Aucune anagramme de « %s » parmi mes 292 000 noms communs — il peut en exister parmi les verbes/"
            "adjectifs, que ce dictionnaire ne couvre pas." % mot)


# RAPPELS « à faire » : « rappelle-moi d'acheter du pain » = une TÂCHE à retenir, pas une question factuelle
# (elle partait en cascade factuelle -> « pas l'information », vécu). Exige de+INFINITIF ou « que … » —
# « rappelle-moi LA capitale de la France » reste une vraie question (re-servir l'info, flux normal).
_RAPPEL_TACHE_RE = re.compile(
    r"^\s*rappelle[- ](?:moi|nous)\s+"
    r"((?:demain|ce\s+soir|apr[eè]s[- ]demain|lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche|"
    r"dans\s+\d+\s+(?:minutes?|heures?|jours?))\s+)?"                       # moment (liste FERMÉE), optionnel
    r"(?:de\s+|d['’]\s*)([a-zà-ÿ]+(?:er|ir|re|oir))\b(.*)$|"
    r"^\s*rappelle[- ](?:moi|nous)\s+que\s+(.+)$", re.IGNORECASE)
_RAPPEL_ALARME_RE = re.compile(
    r"\b(demain|ce\s+soir|cette\s+nuit|tout\s+[àa]\s+l['’]heure|[àa]\s+\d{1,2}\s*h(?:\d{2})?\b|"
    r"dans\s+\d+\s+(?:minutes?|heures?|jours?)|lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)\b", re.I)
_RAPPEL_TODO_RE = re.compile(
    r"\b(?:qu['e]\s*est[- ]ce\s+que\s+je\s+(?:dois|devais)\s+faire|que\s+(?:dois|devais)[- ]je\s+faire|"
    r"mes\s+rappels|ma\s+liste\s+de\s+(?:choses\s+[àa]\s+faire|t[âa]ches)|mes\s+t[âa]ches|"
    r"qu['e]\s*est[- ]ce\s+que\s+je\s+(?:dois|devais)\s+(?:acheter|prendre|apporter))\b", re.I)


def _cap_rappel(texte: str):
    """Accusé HONNÊTE d'un rappel-tâche : Provara n'a PAS d'alarme (aucun démon de notification) — il le dit
    quand un moment est nommé, et promet seulement de RESSERVIR à la demande. FAUX=0 : promesse tenue par le
    stage mémoire (le tour est stocké par le serveur ; le rappel-tâche est ré-servable, cf. _RAPPEL_TACHE_RE)."""
    m = _RAPPEL_TACHE_RE.match(texte.strip())
    if not m:
        return None
    moment = (m.group(1) or "").strip()
    tache = ((m.group(2) or "") + (m.group(3) or "")).strip() if m.group(2) else (m.group(4) or "").strip()
    tache = tache.strip(" ?.!\"'«»")
    if len(tache) < 3:
        return None
    if moment or _RAPPEL_ALARME_RE.search(tache):
        aff = "%s (%s)" % (tache, moment) if moment else tache
        return ("C'est noté : %s. Honnêtement : je n'ai pas d'alarme, je ne peux pas te prévenir tout seul au "
                "bon moment — mais je le garde, et je te le ressers dès que tu me demandes « qu'est-ce que je "
                "devais faire ? »." % aff)
    return ("C'est noté : %s. Demande-moi « qu'est-ce que je devais faire ? » et je te le rappelle." % tache)


_TEXTE_LETTRES_RE = re.compile(
    r"(?:compte\s+les\s+lettres|combien\s+(?:de|y\s+a[- ]t[- ]il\s+de)\s+lettres)\s+(?:dans\s+|a\s+)?"
    r"(?:du\s+mot\s+|le\s+mot\s+|«\s*)?([a-zà-ÿA-ZÀ-Ÿ\-']+)\s*»?\s*\??\s*$", re.I)
# voyelles/consonnes : « combien de voyelles dans chien » OU « le mot chien contient combien de consonnes »
_TEXTE_VOYCONS_A = re.compile(
    r"combien\s+de\s+(voyelles?|consonnes?)\s+(?:dans|a|contient|dans\s+le\s+mot)\s+"
    r"(?:le\s+mot\s+|«\s*)?([a-zà-ÿA-ZÀ-Ÿ\-']+)\s*»?\s*\??\s*$", re.I)
_TEXTE_VOYCONS_B = re.compile(
    r"le\s+mot\s+([a-zà-ÿA-ZÀ-Ÿ\-']+)\s+(?:contient|a|possede)\s+combien\s+de\s+(voyelles?|consonnes?)"
    r"\s*\??\s*$", re.I)
_VOYELLES = set("aeiouyàâäéèêëîïôöùûü")
_TEXTE_ENVERS_RE = re.compile(
    # « inverse/retourne le mot X » (renversement implicite) OU « épelle/écris X à l'envers » (explicite requis)
    r"(?:(?:inverse[rz]?|retourne)\s+(?:le\s+mot\s+|«\s*)?([a-zà-ÿA-ZÀ-Ÿ\-']+)\s*»?"
    r"|(?:[ée]pelle|[ée]cris)\s+(?:le\s+mot\s+|«\s*)?([a-zà-ÿA-ZÀ-Ÿ\-']+)\s*»?\s+[àa]\s+l['’]envers)"
    r"\s*\??\s*$", re.I)
_TEXTE_EPELLE_RE = re.compile(
    r"[ée]pelle(?:[- ]moi)?\s+(?:le\s+mot\s+|«\s*)?([a-zà-ÿA-ZÀ-Ÿ\-']+)\s*»?\s*\??\s*$", re.I)
_TEXTE_ANAG_RE = re.compile(
    r"(?:est[- ]ce\s+que\s+)?«?\s*([a-zà-ÿA-ZÀ-Ÿ\-']+)\s*»?\s+et\s+«?\s*([a-zà-ÿA-ZÀ-Ÿ\-']+)\s*»?\s+"
    r"sont(?:[- ](?:ils|elles))?\s+(?:des\s+)?anagrammes\s*\??\s*$", re.I)
_TEXTE_CASSE_RE = re.compile(
    r"(?:mets?|[ée]cris|convertis)\s+(?:le\s+mot\s+|«\s*)?([a-zà-ÿA-ZÀ-Ÿ\-']+)\s*»?\s+en\s+"
    r"(majuscules?|minuscules?)\s*\??\s*$", re.I)
_TEXTE_MOTS_RE = re.compile(
    r"combien\s+(?:de|y\s+a[- ]t[- ]il\s+de)\s+mots\s+dans\s+(?:la\s+phrase\s+|«\s*)?(.+?)\s*»?\s*\??\s*$", re.I)
_TEXTE_TRI_RE = re.compile(
    r"(?:trie|classe|ordonne|range)\s+(?:les\s+nombres\s+|moi\s+)?((?:d[ée]croissant|d[ée]croissante?s?)\s+)?"
    r"([\d\s,;.\-et]+?)(?:\s+en\s+ordre\s+(d[ée]croissant))?\s*\??\s*$", re.I)


def _cap_texte(texte: str):
    """OPÉRATIONS TEXTUELLES exactes sur UN mot (natif, déterministe — FAUX=0 par construction) : « compte les
    lettres du mot anticonstitutionnellement » -> 25, « épelle chien à l'envers » -> n-e-i-h-c, « épelle chien »,
    « niche et chien sont-ils des anagrammes ? » -> oui (mêmes lettres triées). Un seul MOT exigé (pas de vol
    de questions factuelles) ; l'envers AVANT l'épellation simple (motif plus long d'abord)."""
    t = texte.strip()
    m = _TEXTE_LETTRES_RE.search(t)
    if m:
        mot = m.group(1)
        n = sum(1 for c in mot if c.isalpha())
        return "%d lettres dans « %s »%s." % (n, mot,
                                              "" if n == len(mot) else " (tirets/apostrophes non comptés)")
    for m, gm, gk in ((_TEXTE_VOYCONS_A.search(t), 2, 1), (_TEXTE_VOYCONS_B.search(t), 1, 2)):
        if m:
            mot, kind = m.group(gm), _normalise(m.group(gk))
            lettres = [c for c in _normalise(mot) if c.isalpha()]
            if kind.startswith("voyelle"):
                n = sum(1 for c in lettres if c in _VOYELLES)
                return "« %s » contient %d voyelle%s." % (mot, n, "s" if n != 1 else "")
            n = sum(1 for c in lettres if c not in _VOYELLES)
            return "« %s » contient %d consonne%s." % (mot, n, "s" if n != 1 else "")
    m = _TEXTE_ENVERS_RE.search(t)
    if m:
        mot = m.group(1) or m.group(2)
        return "« %s » à l'envers : %s." % (mot, mot[::-1])
    m = _TEXTE_EPELLE_RE.search(t)
    if m:
        mot = m.group(1)
        if len(mot) < 2:
            return None
        return "« %s » s'épelle : %s." % (mot, "-".join(mot))
    m = _TEXTE_ANAG_RE.search(t)
    if m:
        a, b = m.group(1).lower(), m.group(2).lower()
        cle = lambda w: sorted(c for c in w if c.isalpha())
        if cle(a) == cle(b):
            return "Oui — « %s » et « %s » sont des anagrammes (mêmes lettres)." % (m.group(1), m.group(2))
        return "Non — « %s » et « %s » ne sont pas des anagrammes (lettres différentes)." % (m.group(1), m.group(2))
    m = _TEXTE_CASSE_RE.search(t)
    if m:
        mot, casse = m.group(1), m.group(2).lower()
        return "« %s » en %s : %s." % (mot, "majuscules" if casse.startswith("maj") else "minuscules",
                                       mot.upper() if casse.startswith("maj") else mot.lower())
    m = _TEXTE_MOTS_RE.search(t)
    if m:
        phrase = m.group(1).strip().strip(" ?.!\"'«»")
        mots = phrase.split()
        if mots:
            return "%d mots dans « %s » (séparés par des espaces)." % (len(mots), phrase)
    m = _TEXTE_TRI_RE.search(t)
    if m:
        desc = bool(m.group(1) or m.group(3))
        nums = [x.replace(",", ".") for x in re.findall(r"-?\d+(?:[.,]\d+)?", m.group(2))]
        if len(nums) >= 2:
            vals = sorted((float(x) for x in nums), reverse=desc)
            aff = lambda v: str(int(v)) if v == int(v) else str(v)
            return "Dans l'ordre %s : %s." % ("décroissant" if desc else "croissant",
                                              ", ".join(aff(v) for v in vals))
    # PALINDROME (natif exact — avant : la fiche OBJET répondait « le radar est un système », à côté du mot).
    m = re.search(r"(?:le\s+mot\s+)?([\wà-ÿ-]+)\s+est[- ](?:il|elle|ce)\s+un\s+palindrome"
                  r"|est[- ]ce\s+que\s+(?:le\s+mot\s+)?([\wà-ÿ-]+)\s+est\s+un\s+palindrome", t, re.I)
    if m:
        mot = m.group(1) or m.group(2)
        w = [c for c in _normalise(mot) if c.isalpha()]
        if w and w == w[::-1]:
            return "Oui — « %s » est un palindrome (il se lit pareil dans les deux sens)." % mot
        return "Non — « %s » n'est pas un palindrome (à l'envers : « %s »)." % (mot, mot[::-1])
    # OCCURRENCES D'UNE LETTRE : « combien de fois la lettre s dans mississippi » -> 4 (compte natif).
    m = re.search(r"combien\s+de\s+fois\s+(?:la\s+lettre\s+)?([a-zà-ÿ])\s+dans\s+(?:le\s+mot\s+)?([\wà-ÿ-]+)",
                  t, re.I)
    if m:
        lettre, mot = _normalise(m.group(1)), m.group(2)
        n = sum(1 for c in _normalise(mot) if c == lettre)
        return "%d fois la lettre « %s » dans « %s »." % (n, lettre, mot)
    # CARACTÈRES (tout compris, DIT — les « lettres » ont leur route qui exclut tirets/apostrophes).
    m = re.search(r"combien\s+de\s+caract[eè]res\s+dans\s+(?:le\s+mot\s+)?([\wà-ÿ'-]+)", t, re.I)
    if m:
        mot = m.group(1)
        return "%d caractères dans « %s » (tout signe compris)." % (len(mot), mot)
    # INITIALES : « les initiales de Jean-Claude Van Damme » -> J. C. V. D. (natif ; ≥ 2 mots exigés).
    m = re.search(r"(?:les\s+)?initiales\s+de\s+([\wà-ÿ' -]+?)\s*\??\s*$", t, re.I)
    if m:
        mots_i = [w for w in re.split(r"[\s-]+", m.group(1)) if w and w[0].isalpha()]
        if len(mots_i) >= 2:
            return "%s (initiales de %s)." % (" ".join(w[0].upper() + "." for w in mots_i), m.group(1).strip())
    # PLUS LONG / PLUS COURT MOT : comparaison de longueurs (lettres comptées, natif).
    m = re.search(r"plus\s+(long|court)\s+mot\s+entre\s+([\wà-ÿ-]+)\s+et\s+([\wà-ÿ-]+)", t, re.I)
    if m:
        a, b = m.group(2), m.group(3)
        la, lb = sum(c.isalpha() for c in a), sum(c.isalpha() for c in b)
        if la == lb:
            return "Ils font la même longueur : %d lettres chacun." % la
        gagnant = (a if la > lb else b) if m.group(1).lower() == "long" else (a if la < lb else b)
        return "« %s » (%d lettres contre %d)." % (gagnant, max(la, lb) if m.group(1).lower() == "long"
                                                   else min(la, lb), min(la, lb) if m.group(1).lower() == "long"
                                                   else max(la, lb))
    # REMPLACEMENT DE LETTRE : « remplace les a par des o dans banana » -> bonono (natif exact).
    m = re.search(r"remplace\s+(?:les?\s+|la\s+lettre\s+)?([a-zà-ÿ])\s+par\s+(?:des?\s+|la\s+lettre\s+)?"
                  r"([a-zà-ÿ])\s+dans\s+(?:le\s+mot\s+)?([\wà-ÿ-]+)", t, re.I)
    if m:
        src, dst, mot = m.group(1).lower(), m.group(2).lower(), m.group(3)
        res = mot.replace(src, dst).replace(src.upper(), dst.upper())
        return "« %s » → « %s » (%s remplacé par %s)." % (mot, res, src, dst)
    # TRI DE MOTS : « trie les mots banane, abricot, cerise par ordre alphabétique » (le lexique dumpait ses
    # entrées « abricot (français), abrikosi… », garbage vécu 2026-07-08).
    m = re.search(r"(?:trie|classe|ordonne|range)\s+les\s+mots\s+(.+?)(?:\s+par\s+ordre\s+alphab[eé]tique)?"
                  r"\s*\??\s*$", t, re.I)
    if m:
        mots_t = [w.strip(" ,;.") for w in re.split(r"[,;]|\bet\b", m.group(1)) if w.strip(" ,;.")]
        if len(mots_t) >= 2 and all(" " not in w for w in mots_t):
            return "Ordre alphabétique : %s." % ", ".join(sorted(mots_t, key=_normalise))
    return None


_CONTRAIRE_RE = re.compile(
    r"(?:quel(?:le)?\s+est\s+)?(?:le\s+|l['’]\s*)?(?:contraire|oppos[ée]|antonyme)\s+"
    r"(?:de\s+|du\s+|d['’]\s*)(?:la\s+|le\s+|l['’]\s*)?(.+?)\s*\??\s*$", re.I)


def _cap_contraire(texte: str):
    """« quel est le contraire de grand ? » -> petit. Réseau lexical JeuxDeMots embarqué (synonymes.contraires,
    fonction qui existait sans être câblée). Le contraire CANONIQUE est celui dont la relation est RÉCIPROQUE
    (petit∈contraires(grand) ET grand∈contraires(petit)) ; les autres sont listés en complément. FAUX=0 :
    relation lexicale sourcée, mot inconnu -> None."""
    m = _CONTRAIRE_RE.search(texte.strip())
    if not m:
        return None
    mot = _strip_article(m.group(1).strip().strip(" ?.!\"'«»"))
    if not mot or len(mot) < 2 or " " in mot:
        return None
    try:
        import synonymes as _SYN
        if not _SYN.disponible():
            return None
        cs = _SYN.contraires(mot)
        if not cs:
            return None
        if len(cs) == 1:
            return "Le contraire de « %s » : %s — réseau lexical JeuxDeMots." % (mot, cs[0])
        return ("Contraires de « %s » d'après mon réseau lexical (JeuxDeMots) : %s."
                % (mot, ", ".join(cs[:6])))
    except Exception:
        return None


_FAITS_BIO = None                 # {(entite_norm, attribut_norm): (valeur, note)} — seed curé (validé Yohan)
_BIO_RE = re.compile(
    r"combien\s+(?:de\s+|d['’]?\s*)?(chromosomes?|pattes?|bras|os|dents?|c[œoe]urs?|cavit[ée]s?|vies?)\s+"
    r"(?:a|poss[eè]de|compte|ont?)\s+(?:un\s+|une\s+|le\s+|la\s+|l['’]?\s*)?(.+?)\s*\??\s*$", re.I)


def _cap_fait_bio(texte: str):
    """« combien de chromosomes a l'être humain ? » -> 46 (23 paires). Seed CURÉ de faits biologiques
    incontestables (src/faits_bio_seed.jsonl, validé par Yohan) — la précision utile est dite (l'araignée est
    un arachnide ; les « 9 vies » du chat sont une légende). FAUX=0 : hors seed -> None."""
    global _FAITS_BIO
    m = _BIO_RE.search(texte)
    if not m:
        return None
    if _FAITS_BIO is None:
        _FAITS_BIO = {}
        try:
            import json as _json
            chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "faits_bio_seed.jsonl")
            if not os.path.exists(chemin):                    # bundle .exe : src/ est sur sys.path via _MEIPASS
                import fleuve_ville as _FVmod
                chemin = os.path.join(os.path.dirname(os.path.abspath(_FVmod.__file__)), "faits_bio_seed.jsonl")
            with open(chemin, encoding="utf-8") as fh:
                for ligne in fh:
                    try:
                        o = _json.loads(ligne)
                    except ValueError:
                        continue
                    if o.get("entite") and o.get("attribut") and "_relation" not in o:
                        _FAITS_BIO[(_normalise(o["entite"]), _normalise(o["attribut"]))] = (
                            str(o.get("valeur")), o.get("note") or "")
        except OSError:
            pass
    attr = _normalise(m.group(1))
    attr = {"chromosome": "chromosomes", "patte": "pattes", "dent": "dents", "coeur": "coeurs",
            "cœur": "coeurs", "vie": "vies", "cavite": "cavites"}.get(attr.rstrip("s") if attr not in
            ("bras", "os") else attr, attr)
    ent = _normalise(_strip_article(m.group(2).strip()))
    cell = _FAITS_BIO.get((ent, attr)) or _FAITS_BIO.get((ent, attr.rstrip("s")))
    if not cell:
        return None
    val, note = cell
    suffixe = " (%s)" % note if note else ""
    mot = m.group(1).lower()
    if val.strip() in ("0", "1") and mot.endswith("s") and mot not in ("bras", "os"):
        mot = mot[:-1]                                        # « 1 vie », pas « 1 vies »
    return "%s %s%s." % (val, mot, suffixe)


_PROTONS_RE = re.compile(
    r"combien\s+(?:de\s+|d['’]?\s*)?(protons?|[ée]lectrons?)\s+(?:(?:a|poss[eè]de|contient|compte|y\s+a[- ]t[- ]il)\s+"
    r"(?:dans\s+)?|dans\s+)"
    r"(?:le\s+|la\s+|l['’]?\s*)?(.+?)\s*\??\s*$", re.I)


def _cap_protons(texte: str):
    """« combien de protons a l'hydrogène ? » -> 1 : le nombre de protons EST le numéro atomique Z (définition),
    stocké dans numero_atomique (118 éléments confirmés). Électrons : égaux aux protons pour l'atome NEUTRE
    (précisé dans la réponse). FAUX=0 : valeur relue, hors éléments -> None."""
    m = _PROTONS_RE.search(texte)
    if not m:
        return None
    cell = _charge_direct("numero_atomique").get(_normalise(_strip_article(m.group(2).strip())))
    if not cell:
        return None
    aff, z = cell
    plur = "s" if str(z).strip() not in ("1", "0") else ""
    if _normalise(m.group(1)).startswith("proton"):
        return "%s : %s proton%s — le numéro atomique Z (c'est sa définition)." % (aff[:1].upper() + aff[1:], z, plur)
    return ("%s : %s électron%s pour l'atome NEUTRE (autant que de protons, Z = %s)."
            % (aff[:1].upper() + aff[1:], z, plur, z))


_LUNES_RE = re.compile(
    r"combien\s+(?:de\s+|d['’]\s*)?(?:lunes?|satellites?(?:\s+naturels?)?)\s+"
    r"(?:a|poss[eè]de|compte|orbitent\s+autour\s+de)\s+(?:la\s+plan[eè]te\s+)?(?:la\s+|le\s+|l['’]\s*)?"
    r"(.+?)\s*\??\s*$", re.I)


def _cap_lunes(texte: str):
    """« combien de lunes a Mars ? » -> « 2 dans mes données : Phobos, Déimos ». Compte RÉEL des corps dont le
    parent orbital stocké (corps_parent_astre) est la cible. HONNÊTE : « dans mes données » — la table n'est pas
    exhaustive pour les géantes (Jupiter en a 95 connues). FAUX=0 : entités réelles listées, cible inconnue -> None."""
    m = _LUNES_RE.search(texte)
    if not m:
        return None
    cible = _normalise(_strip_article(m.group(1).strip()))
    if not cible or len(cible) < 3:
        return None
    par = _charge_direct("corps_parent_astre")
    if not par:
        return None
    lunes = sorted(aff for aff, parent in par.values() if _normalise(parent) == cible)
    connu = cible in par or any(_normalise(p) == cible for _a, p in par.values())
    if not connu:
        return None
    if not lunes:
        return "Aucune dans mes données (ce qui ne prouve pas qu'il n'y en a pas — ma table orbitale est partielle)."
    return "%d dans mes données : %s. (Ma table orbitale n'est pas exhaustive.)" % (len(lunes), ", ".join(lunes))


def _cap_orbite(texte: str):
    """SOMMET : la machine DÉCOUVRE une règle puis l'APPLIQUE avec preuve. « Phobos fait-il partie du système
    solaire ? » -> la relation `corps_parent_astre` (corps -> corps directement orbité) : la machine INDUIT que
    « orbiter » est transitive (cohérente avec toutes les données) et REJETTE la symétrie (sinon le Soleil orbiterait
    la Terre), puis DÉRIVE Phobos -> Mars -> Soleil. FAUX=0 : la conclusion n'est servie qu'avec sa CHAÎNE de faits
    vérifiés montrée (chaque maillon re-vérifiable) ; sinon None."""
    cible = None
    m = _SYSTEME_RE.search(texte)
    if m:
        sujet = _strip_article(m.group(1).strip())
        cible = "soleil" if m.group(2) else _normalise(_strip_article((m.group(3) or "").strip()))
    else:
        m = _ORBITE_RE.search(texte)
        if not m:
            return None
        sujet, cible = _strip_article(m.group(1).strip()), _normalise(_strip_article(m.group(2).strip()))
    ns = _normalise(sujet)
    if not ns or not cible or len(ns) < 2:
        return None
    par = _charge_direct("corps_parent_astre")         # {corps_norm : (corps_affiché, corps_parent)}
    if not par:
        return None
    _ASTRO_ART = {"soleil": "le Soleil", "terre": "la Terre", "lune": "la Lune"}

    def _chaine_vers(depart, but):
        # marche la chaîne parentale depart -> parent -> ... ; liste affichée si but atteint, sinon None
        if depart not in par:
            return None
        chaine = [par[depart][0]]
        vus, cur = {depart}, depart
        for _ in range(20):
            cell = par.get(cur)
            if not cell:
                return None
            parent = cell[1]
            chaine.append(parent)
            np = _normalise(parent)
            if np == but:
                return chaine
            if np in vus:
                return None
            vus.add(np)
            cur = np
        return None

    def _aff(chaine):
        return [_ASTRO_ART.get(_normalise(c), c) for c in chaine]

    chaine = _chaine_vers(ns, cible)
    if chaine and len(chaine) == 2:                     # relation DIRECTE : fait stocké, servi tel quel
        a, b = _aff(chaine)
        return "Oui — c'est un fait vérifié dans mes données : %s orbite %s." % (a, b)
    if chaine:
        # DÉCOUVERTE : on valide la transitivité (cohérente) et on rejette la symétrie, pour l'afficher
        note = ""
        try:
            import induction_horn as _IH
            paires = {(_normalise(k), _normalise(v[1])) for k, v in par.items()}
            neg = {(y, x) for (x, y) in paires}
            ev_t = _IH.evalue(_IH.TRANSITIVITE, paires, neg)
            ev_s = _IH.evalue(_IH.SYMETRIE, paires, neg)
            if ev_t["consistante"] and not ev_s["consistante"]:
                cx = sorted(ev_s["viole"])[0]
                aff = lambda z: (par[z][0] if z in par else z.capitalize())
                note = (" (règle que j'ai découverte : « orbiter » est transitive — cohérente avec les %d faits — "
                        "mais PAS symétrique, sinon %s orbiterait %s)" % (len(paires), aff(cx[0]), aff(cx[1])))
        except Exception:
            pass
        chaine = _aff(chaine)
        derivation = "%s orbite %s" % (chaine[0], ", qui orbite ".join(chaine[1:]))
        return "Oui — je le déduis : %s%s." % (derivation, note)
    # sens INVERSE vérifié (« le Soleil tourne-t-il autour de la Terre ? ») : « orbiter » n'est pas
    # symétrique (règle induite) -> Non sûr, la chaîne réelle montrée
    inverse = _chaine_vers(cible, ns)
    if inverse:
        inv = _aff(inverse)
        return "Non — c'est l'inverse : %s orbite %s." % (inv[0], ", qui orbite ".join(inv[1:]))
    # sujet astro connu, cible astro connue, mais AUCUNE chaîne : montrer le fait réel plutôt que
    # laisser la question filer vers la cascade lourde (risque de hors-sujet type FAUX)
    if ns in par and (cible in par or any(_normalise(v[1]) == cible for v in par.values())):
        a = _ASTRO_ART.get(ns, par[ns][0])
        b = _ASTRO_ART.get(_normalise(par[ns][1]), par[ns][1])
        return ("D'après mes données, %s orbite %s — je n'ai aucun fait vérifié reliant %s à « %s »."
                % (a, b, a, cible))
    return None


# ————— TRANSITIVITÉ GÉNÉRALISÉE (au-delà de l'astronomie) : fermetures transitives SÛRES par domaine —————
# Chaque groupe fusionne des relations parentales chaînables des données ; la conclusion emploie le VERBE DE
# FERMETURE (« les eaux rejoignent », « fait partie du groupe ») — définitionnellement vrai le long d'une chaîne
# de faits stockés, montrée en entier (chaque maillon re-vérifiable). GARDE ANTI-HOMONYME : un nom porté par
# PLUSIEURS entités (valeurs parentales distinctes) est INTRAVERSABLE — on refuse la chaîne plutôt que risquer
# un faux (FAUX=0). Candidats REJETÉS après audit des données (2026-07-04) : subdivision_localite (homonymes
# inter-pays -> chaînes absurdes « Rivers -> Iowa »), montagne_pic_parent (parent de PROÉMINENCE topographique,
# pas une appartenance), généalogie mere/pere_personne (homonymes royaux non désambiguïsés, « Louis de France »).
# corps_parent_astre reste servi par _cap_orbite (avec sa note de règle découverte).
_TRANS_GROUPES = (
    dict(cle="hydro", rels=("embouchure_ruisseau", "embouchure_canal", "embouchure_fleuve"),
         lien="se jette dans", conclusion="donc les eaux %s rejoignent bien %s", articles=True),
    dict(cle="groupe", rels=("maison_mere",),                       # pas d'articles : « le 105 Music » serait faux
         lien="a pour maison mère", conclusion="donc %s fait bien partie du groupe %s", articles=False),
    # CONFLITS militaires (mereologie « fait partie de ») : bataille -> opération -> front -> guerre. Quasi
    # fonctionnel (3 ambigus / 5853 -> gardés par la garde anti-homonyme). Chaînes réelles de profondeur 3-4
    # (« opération Tonga -> débarquement de Normandie -> bataille de Normandie -> front de l'Ouest »).
    dict(cle="conflit", rels=("conflit_parent_bataille", "conflit_parent_operation_militaire",
                              "conflit_parent_siege"),
         lien="fait partie de", conclusion="donc %s fait bien partie de %s", articles=False),
)
_TRANS_HYDRO_RE = re.compile(
    r"^(?:est ce que )?(?:le |la |les |l )?(.+?) (?:se jette(?:nt)?|se deverse(?:nt)?|debouche(?:nt)?|"
    r"finit|finissent|rejoint|rejoignent|termine(?:nt)?)"
    r"(?: t (?:il|elle))?(?: elles?)? (?:dans|sur|a|au|en) (?:le |la |les |l )?(.+?)\s*$")
_TRANS_GROUPE_RE = re.compile(
    r"^(?:est ce que )?(?:le |la |les |l )?(.+?) (?:fait(?: t)?(?: il| elle)? partie|"
    r"appartient(?: t)?(?: il| elle)?) (?:du |de |des |au |a |aux )+(?:groupe )?(.+?)\s*$")
_TRANS_CACHE: dict = {}
# « de quel conflit / quelle guerre / quel front / quelle bataille fait partie <X> ? » (question ASCENDANTE).
_TRANS_CONFLIT_OUVERT_RE = re.compile(
    r"^(?:de |dans )?quel(?:le)?s? (?:conflit|guerre|front|bataille|operation|campagne|offensive)s? "
    r"(?:fait(?: t)?(?: il| elle)? partie|englobe|contient|inclut|comprend) (?:le |la |les |l |du |de |des )?(.+?)\s*$")


def _conflit_ascendant(sujet: str):
    """Remonte la chaîne mereologique des conflits depuis `sujet` jusqu'au sommet (« bataille de Marignan » ->
    « guerre de la Ligue de Cambrai ») et renvoie la dérivation. FAUX=0 : chaîne de faits stockés, garde
    anti-homonyme (un nom à plusieurs parents est intraversable) ; None si le sujet n'est pas une entité connue."""
    groupe = next(g for g in _TRANS_GROUPES if g["cle"] == "conflit")
    par, ambigu = _charge_transitif(groupe)
    ns = _normalise(_strip_article(sujet))
    if not ns or ns not in par:
        return None
    chaine = [par[ns][0]]
    cur, vus = ns, {ns}
    for _ in range(25):
        if cur in ambigu:                        # homonyme -> intraversable (FAUX=0)
            break
        cell = par.get(cur)
        if not cell:
            break
        chaine.append(cell[1])
        cur = cell[2]
        if cur in vus:
            break
        vus.add(cur)
    if len(chaine) < 2:
        return None
    sommet = chaine[-1]
    tete = chaine[0][:1].upper() + chaine[0][1:]
    if len(chaine) == 2:                          # un seul saut : réponse directe
        return "%s fait partie de %s." % (tete, sommet)
    derivation = " → ".join(chaine)
    return "%s fait partie de %s.\nLa chaîne complète : %s." % (tete, sommet, derivation)


def _charge_transitif(groupe: dict):
    """Carte parentale FUSIONNÉE du groupe {norm : (entité_affichée, parent_affiché, parent_norm)} + ensemble des
    noms AMBIGUS (un même nom -> plusieurs parents distincts : homonymes, intraversables). Chargée une fois."""
    cle = groupe["cle"]
    if cle in _TRANS_CACHE:
        return _TRANS_CACHE[cle]
    par, valeurs = {}, {}
    for rel in groupe["rels"]:
        chemin = os.path.join(_DOSSIER_LECTEUR, rel + ".jsonl")
        try:
            with open(chemin, encoding="utf-8") as fh:
                for ligne in fh:
                    ligne = ligne.strip()
                    if not ligne:
                        continue
                    try:
                        obj = json.loads(ligne)
                    except ValueError:
                        continue
                    if "_relation" in obj:
                        continue
                    e, v = obj.get("entite"), obj.get("valeur")
                    if e and v:
                        ne, nv = _normalise(e), _normalise(v)
                        valeurs.setdefault(ne, set()).add(nv)
                        par[ne] = (str(e), str(v), nv)
        except OSError:
            continue
    ambigu = frozenset(k for k, s in valeurs.items() if len(s) > 1)
    _TRANS_CACHE[cle] = (par, ambigu)
    return _TRANS_CACHE[cle]


# SYLLOGISME À PRÉMISSES FOURNIES (audit 2026-07-08 : « si tous les mammifères allaitent et que le chat est un
# mammifère, que peut-on en déduire ? » partait au DÉCOUPAGE multi-questions — trois « je ne l'ai pas en
# mémoire »). Barbara / modus ponens DANS les prémisses de l'utilisateur : la conclusion est TYPÉE « d'après
# TES prémisses » (jamais posée comme un fait Provara) ; si le store CORROBORE la mineure (est_un), on le DIT —
# la déduction devient doublement ancrée. Un moyen terme qui ne se noue pas -> refus expliqué (pas de garbage).
_SYLLO_RE = re.compile(
    # « si » optionnel, prémisses reliées par « et que » OU une virgule/point, question finale « que peut-on
    # en déduire » OU directe « Félix est-il gris ? » (vécu 2026-07-08 : la forme interrogative tombait en mémo).
    r"\b(?:si\s+)?tou(?:s|tes)\s+les\s+([\wà-ÿ-]+)\s+(sont\s+[\wà-ÿ' -]+?|[\wà-ÿ-]+ent)\s*"
    r"(?:et\s+qu[e'’]|[,.;]\s*(?:et\s+qu[e'’]\s*)?)\s*"
    r"((?:le\s+|la\s+|l['’]\s*|un\s+|une\s+)?[\wà-ÿ' -]+?)\s+est\s+un[e]?\s+([\wà-ÿ-]+)\b"
    r".*?\b(?:d[ée]duire|conclure|conclusions?|est[- ](?:il|elle|ce)|alors)\b", re.I | re.S)


# THÉORIE DES JEUX — jeux classiques (câblage « tout câbler » 2026-07-08) : le module `jeux_appliques` CALCULE
# les équilibres de Nash purs de jeux 2×2 DÉFINIS (objets mathématiques, pas des données contestables). On câble
# les trois canoniques. FAUX=0 : verdict issu du module vérifié ; jeu non catalogué -> None (pas de fabrication).
_JEUX_CLASSIQUES = {
    "prisonnier": ("dilemme_prisonnier", "du dilemme du prisonnier", "Le dilemme du prisonnier"),
    "sexes": ("bataille_des_sexes", "de la bataille des sexes", "La bataille des sexes"),
    "pennies": ("matching_pennies", "du matching pennies", "Le matching pennies"),
    "pieces": ("matching_pennies", "du matching pennies", "Le matching pennies"),
}
_JEUX_RE = re.compile(r"\b(nash|[ée]quilibre|jeu|dilemme|strat[ée]gie dominante)\b", re.I)


def _cap_jeux(texte: str):
    """Équilibre de Nash d'un jeu CLASSIQUE nommé (« équilibre de Nash du dilemme du prisonnier »). Verdict
    calculé par `jeux_appliques` (vérifié). None si aucun jeu catalogué n'est nommé (FAUX=0, pas d'invention)."""
    if not _JEUX_RE.search(texte):
        return None
    n = _normalise(texte)
    cle = next((k for k in _JEUX_CLASSIQUES if k in n), None)
    if cle is None:
        return None
    fn_nom, de_jeu, le_jeu = _JEUX_CLASSIQUES[cle]
    try:
        import jeux_appliques as _J
        d = getattr(_J, fn_nom)()
    except Exception:
        return None
    actions = d.get("actions")
    eqs = d.get("equilibres_nash") or []

    def _profil(p):
        if actions and len(actions) == 2:
            return "(%s, %s)" % (actions[p[0]], actions[p[1]])
        return str(tuple(p))

    if not eqs:
        return ("%s n'a PAS d'équilibre de Nash en stratégies pures (il en a un en stratégies mixtes). "
                "Calcul vérifié." % le_jeu)
    profils = ", ".join(_profil(p) for p in eqs)
    txt = "Équilibre de Nash (pur) %s : %s." % (de_jeu, profils)
    if d.get("equilibre_pareto_domine"):
        txt += (" C'est le paradoxe : cet équilibre est Pareto-dominé — les deux gagneraient plus en coopérant, "
                "mais trahir est la stratégie dominante de chacun.")
    return txt


def _verbe_singulier(v: str) -> str:
    """« allaitent » -> « allaite », « sont mortels » -> « est mortel », « sont des X » -> « est un X »
    (accord de la conclusion — règles sûres du pluriel régulier, jamais une invention de forme)."""
    v = v.strip()
    if v.lower().startswith("sont "):
        reste = v[5:].strip()
        if re.match(r"^des\s+", reste, flags=re.I):
            reste = re.sub(r"^des\s+", "un ", reste, flags=re.I)
        mots = reste.split()
        # mots dont le SINGULIER finit déjà en -s (invariables) : « gris » devenait « gri » (vécu 2026-07-08)
        _INVAR_S = {"gris", "gros", "frais", "mauvais", "bas", "las", "epais", "épais", "precis", "précis",
                    "francais", "français", "anglais", "confus", "divers", "gras", "ras", "clos", "assis"}
        if mots:                                         # pluriels réguliers : -eaux -> -eau, -aux -> -al, -s -> ∅
            if mots[-1].lower() in _INVAR_S:
                pass
            elif mots[-1].endswith("eaux"):
                mots[-1] = mots[-1][:-1]
            elif mots[-1].endswith("aux"):
                mots[-1] = mots[-1][:-3] + "al"
            elif mots[-1].endswith("s") and not mots[-1].endswith("ss"):
                mots[-1] = mots[-1][:-1]
        return "est " + " ".join(mots)
    return (v[:-3] + "e") if v.lower().endswith("ent") else v


# LOGIQUE PROPOSITIONNELLE (câblage « tout câbler » 2026-07-08) : « si A alors B, or …, donc … » -> Provara
# JUGE la validité de l'inférence (modus ponens/tollens = valide ; affirmation du conséquent / négation de
# l'antécédent = sophisme formel), verdict issu du module VÉRIFIÉ `sophismes`. FAUX=0 : logique formelle exacte ;
# structure ambiguë -> None (abstention). Complète `_cap_syllogisme` (catégoriel « tous les A ») par le CONDITIONNEL.
_LOGIQUE_RE = re.compile(
    r"\bsi\s+(.+?)\s+alors\s+(.+?)\s*[,;.]\s*(?:or|et|mais)\s+(.+?)\s*[,;.]\s*"
    r"(?:donc|alors|par\s+cons[eé]quent)\s+(.+?)\s*[?.]?\s*$", re.I)
_LOG_STOP = frozenset("le la les un une des de du d et est sont a l en ce que qui il elle on se sa son ne".split())
_LOG_NEG_RE = re.compile(r"\bne\b|\bn |\bpas\b|\bnon\b|\baucun", re.I)


def _cap_logique(texte: str):
    """Validité d'un raisonnement conditionnel en langage naturel (modus ponens/tollens vs sophismes formels).
    Réutilise `sophismes.identifie_forme`/`est_valide` (vérifié). None si la structure n'est pas nette (FAUX=0)."""
    m = _LOGIQUE_RE.search(texte)
    if not m:
        return None
    A, B, mineure, concl = m.group(1), m.group(2), m.group(3), m.group(4)
    mA = set(w for w in _normalise(A).split() if len(w) > 2 and w not in _LOG_STOP)
    mB = set(w for w in _normalise(B).split() if len(w) > 2 and w not in _LOG_STOP)
    if not mA or not mB:
        return None

    def classe(prop):
        sansneg = _LOG_NEG_RE.sub(" ", _normalise(prop))
        w = set(sansneg.split())
        sa, sb = len(w & mA), len(w & mB)
        if sa == 0 and sb == 0:
            return None
        return ("a" if sa >= sb else "b", bool(_LOG_NEG_RE.search(_normalise(prop))))

    cm, cc = classe(mineure), classe(concl)
    if not cm or not cc:
        return None
    lit = lambda c: ("~" if c[1] else "") + c[0]
    try:
        import sophismes as _SO
        forme = _SO.identifie_forme("a->b", lit(cm), lit(cc))
        valide = _SO.est_valide(forme)
    except Exception:
        return None
    noms = {"modus_ponens": "modus ponens", "modus_tollens": "modus tollens",
            "affirmation_consequent": "affirmation du conséquent", "negation_antecedent": "négation de l'antécédent"}
    if valide:
        return ("Raisonnement VALIDE (%s) : la conclusion découle logiquement de tes prémisses. "
                "Je juge la FORME, pas la vérité des prémisses." % noms.get(forme, forme))
    return ("Raisonnement INVALIDE — c'est un sophisme formel : %s. La conclusion NE découle pas des prémisses "
            "(même si elle pouvait être vraie par ailleurs). Je juge la forme, pas le fond." % noms.get(forme, forme))


def _cap_syllogisme(texte: str):
    """Syllogisme explicite (« si tous les A V… et que C est un A, que peut-on en déduire ? ») -> conclusion
    dans LES PRÉMISSES DE L'UTILISATEUR, typée comme telle (mode hypothétique balisé — jamais un fait servi).
    FAUX=0 : la seule affirmation Provara éventuelle est la CORROBORATION de la mineure par le store (est_un)."""
    m = _SYLLO_RE.search(texte)
    if not m:
        return None
    a, verbe, c, a2 = m.group(1), m.group(2), m.group(3).strip(" '’"), m.group(4)
    c_nu = re.sub(r"^(?:le|la|l['’]?|un|une)\s+", "", c, flags=re.I).strip()  # lookup nu ; l'article de
    if _normalise(a).rstrip("s") != _normalise(a2).rstrip("s"):               # l'utilisateur est GARDÉ à l'affichage
        return ("Je vois deux prémisses, mais le moyen terme ne se noue pas (« %s » d'un côté, « %s » de "
                "l'autre) — le syllogisme est invalide, je ne déduis rien plutôt que de forcer." % (a, a2))
    corro = ""
    try:
        import est_un as _EUS
        if _EUS.est_un(c_nu, a2) or _EUS.est_un(c_nu, a):
            corro = " — et mes faits CORROBORENT la seconde (%s → %s, vérifié dans ma base)" % (c_nu, a2)
    except Exception:
        pass
    return ("D'après TES prémisses (syllogisme en Barbara / modus ponens) : %s %s. "
            "Je raisonne ICI dans tes prémisses, je ne les pose pas comme des faits%s."
            % (c, _verbe_singulier(verbe), corro))


def _cap_transitif(texte: str):
    """TRANSITIVITÉ GÉNÉRALISÉE : « est-ce que la Lukna finit dans la mer Baltique ? » -> la machine marche la
    chaîne hydrographique RÉELLE (Lukna -> Merkys -> Niémen -> mer Baltique) et répond avec la dérivation complète ;
    « 105 Music fait-elle partie du groupe Sony ? » -> chaîne des maisons mères. FAUX=0 : uniquement des chaînes de
    faits stockés, montrées ; noms homonymes intraversables ; sinon None (le fait direct suit la voie normale)."""
    qn = _normalise(texte).strip().rstrip(" ?")
    essais = []
    m = _TRANS_HYDRO_RE.match(qn)
    if m:
        essais.append(("hydro", m.group(1), m.group(2)))
    m = _TRANS_GROUPE_RE.match(qn)
    if m:
        essais.append(("groupe", m.group(1), m.group(2)))
        essais.append(("conflit", m.group(1), m.group(2)))   # « fait partie de » vaut aussi pour les conflits
    # QUESTION OUVERTE conflit : « de quel conflit / quelle guerre / quelle bataille fait partie X ? » -> on
    # REMONTE la chaîne jusqu'au sommet et on renvoie la dérivation (pas une vérification oui/non).
    mo = _TRANS_CONFLIT_OUVERT_RE.match(qn)
    if mo:
        return _conflit_ascendant(mo.group(1))
    for cle, sujet, cible in essais:
        groupe = next(g for g in _TRANS_GROUPES if g["cle"] == cle)
        par, ambigu = _charge_transitif(groupe)
        ns = _normalise(_strip_article(sujet))
        nc = _normalise(_strip_article(cible))
        if not ns or not nc or ns not in par:
            continue
        chaine = [par[ns][0]]
        cur, vus, atteint = ns, {ns}, False
        for _ in range(25):
            if cur in ambigu:                    # nom porté par plusieurs entités -> hop intraversable (FAUX=0)
                break
            cell = par.get(cur)
            if not cell:
                break
            chaine.append(cell[1])
            if cell[2] == nc:
                atteint = True
                break
            cur = cell[2]
            if cur in vus:                       # cycle de données -> on s'arrête proprement
                break
            vus.add(cur)
        # < 2 sauts = fait direct : pour hydro/groupe il est servi par la voie normale (on exige une dérivation) ;
        # pour conflit la relation n'existe NULLE PART ailleurs -> on sert même le lien direct (1 saut).
        min_maillons = 2 if cle == "conflit" else 3
        if not atteint or len(chaine) < min_maillons:
            continue
        a_conclu, b_conclu = chaine[0], chaine[-1]
        if groupe.get("articles"):               # français soigné : « la Lukna », « le Merkys », « la mer Baltique »
            try:                                 # et conclusion CONTRACTÉE : « les eaux du Lukna »
                import realisation_fr as _RF
                a_conclu, b_conclu = _RF.de_syntagme(chaine[0]), _RF.le_syntagme(chaine[-1])
                chaine = [_RF.le_syntagme(c) for c in chaine]
            except Exception:
                pass
        derivation = ("%s %s " % (chaine[0], groupe["lien"])) + (", qui %s " % groupe["lien"]).join(chaine[1:])
        return "Oui — je le déduis : %s — %s." % (derivation,
                                                  groupe["conclusion"] % (a_conclu, b_conclu))
    return None


def _cap_deduction(texte: str):
    """RAISONNEMENT DÉDUCTIF PROUVÉ (moteur Datalog `deduction.py`) : dérive un fait qui n'est stocké NULLE PART et
    MONTRE sa preuve. Ex. « sur quel continent se trouve Abuja ? » -> Afrique, dérivé de « Abuja est la capitale du
    Nigéria » + « le Nigéria est en Afrique » via une règle. FAUX=0 : ne rend que ce qui est logiquement ENTRAÎNÉ par
    des faits vérifiés (sinon None) ; la provenance rend chaque dérivation re-vérifiable. C'est la pensée machine qui
    dépasse le simple lookup : un fait NON écrit devient connu et prouvé."""
    m = _DERIV_CONT_VILLE_RE.search(texte)
    if not m:
        return None
    try:
        import deduction as _D
    except Exception:
        return None
    ville = _strip_article(m.group(1).strip())
    nv = _normalise(ville)
    if not nv or len(nv) < 2:
        return None
    hit = _charge_reverse("capitale").get(nv)          # quel(s) pays a/ont cette ville pour capitale ?
    if not hit or not hit[1]:
        return None
    ville_aff = hit[0]
    moteur = _D.MoteurDeduction()
    phrase = {}                                        # triplet de base -> phrase FR (pour la preuve)
    cont_aff = {}                                      # continent normalisé -> forme affichée
    for pays in hit[1]:
        np = _normalise(pays)
        cont = _charge_direct("continent").get(np)
        if not cont:
            continue
        cv = _normalise(cont[1])
        pays_aff = cont[0]                              # forme ACCENTUÉE (« Nigéria »), pas celle de capitale.jsonl
        moteur.ajoute_fait("capitale", np, nv, "capitale")
        moteur.ajoute_fait("continent", np, cv, "continent")
        try:
            import realisation_fr as _RF
            de_pays, le_pays = _RF.de_pays(pays_aff), _RF.article_pays(pays_aff)
        except Exception:
            de_pays, le_pays = "de " + pays_aff, pays_aff
        phrase[("capitale", np, nv)] = "%s est la capitale %s" % (ville_aff, de_pays)
        phrase[("continent", np, cv)] = "%s est en %s" % (le_pays, cont[1])
        cont_aff[cv] = cont[1]
    #   RÈGLE : le continent d'une ville-capitale = le continent de son pays  (fait dérivé, non stocké)
    moteur.ajoute_regle(("continent_ville", "V", "C"),
                        (("capitale", "P", "V"), ("continent", "P", "C")), nom="continent-via-pays")
    reps = moteur.reponses("continent_ville", nv)
    if not reps:
        return None
    cnorm, prov = reps[0]
    _regle, supports = prov[0]
    preuve = " et ".join(phrase[s] for s in supports if s in phrase)
    return "%s — je le déduis : %s." % (cont_aff.get(cnorm, cnorm.capitalize()), preuve)


_PORTRAIT_RE = re.compile(
    r"^\s*(?:parle[- ]?moi\s+d[eu'’]|pr[ée]sente[- ]?(?:moi\s+)?|d[ée]cris[- ]?(?:moi\s+)?"
    r"|dis[- ]?m['’]?en\s+plus\s+sur\s+|dis[- ]?moi\s+tout\s+sur\s+|dis[- ]?moi\s+sur\s+"
    r"|que\s+sais[- ]?tu\s+(?:sur|de|d['’])\s*|qu['’]?\s*sais[- ]?tu\s+(?:sur|de|d['’])\s*"
    r"|raconte[- ]?moi\s+|parle[- ]?moi\s+de\s+)"
    r"(?:la\s+|le\s+|les\s+|l['’]|un\s+|une\s+)?(.+?)\s*\??\s*$", re.I)


def _cap_portrait(texte: str):
    """RÉPONSE DÉVELOPPÉE (« parle-moi du Nigéria ») : assemble PLUSIEURS faits vérifiés + un INSIGHT calculé (rang
    dans son continent). Profondeur par la LARGEUR, pas par la génération — chaque brique est vérifiable (FAUX=0).
    Gate : ne se déclenche que pour un PAYS connu (relation `continent`) ; sinon None -> definition/fiche prennent le relais."""
    m = _PORTRAIT_RE.match(texte)
    if m:
        ent_txt = m.group(1)
    elif _veut_profondeur(texte):
        # DEMANDE DE PROFONDEUR sur une entité (« explique-moi le Japon », « détaille la France ») -> portrait développé
        m2 = re.search(r"(?:explique|d[ée]taille|d[ée]veloppe|approfondis?|[ée]labore)\S*\s+(?:moi\s+)?"
                       r"(?:sur\s+|de\s+|d['’])?(?:la\s+|le\s+|les\s+|l['’])?(.+?)\s*\??\s*$", texte, re.I)
        ent_txt = m2.group(1) if m2 else None
        if not ent_txt:
            return None
    else:
        return None
    ne = _normalise(_strip_article(ent_txt.strip()))
    cont = _charge_direct("continent").get(ne)
    if not cont:
        return None
    nom, continent = cont[0], cont[1]
    try:
        import realisation_fr as _RF
        sujet = _RF.article_pays(nom, majuscule=True)          # « La France », « Le Nigéria », « L'Italie »
        de_cont = _RF.de(continent, continent=True)            # « d'Afrique », « d'Europe »
    except Exception:
        sujet, de_cont = nom, "de " + continent
    phrases = ["%s est un pays %s" % (sujet, de_cont)]
    cap = _charge_direct("capitale").get(ne)
    if cap:
        phrases[0] += ", dont la capitale est %s" % cap[1]
    phrases[0] += "."
    pop = _charge_direct("population_pays").get(ne)
    if pop and _nombre(pop[1]) is not None:
        n = int(_nombre(pop[1]))
        rang = None
        paires, _ = _membres_attribut("pays", continent, "peuple")
        if paires:
            for i, (e, _v) in enumerate(paires):
                if _normalise(e) == ne:
                    rang = (i + 1, len(paires))
                    break
        s_pop = "Sa population est d'environ %s habitants" % format(n, ",d").replace(",", " ")
        if rang and rang[0] == 1:
            s_pop += " — c'est le pays le plus peuplé %s" % de_cont
        elif rang:
            s_pop += " (le %dᵉ plus peuplé de son continent sur %d)" % rang
        phrases.append(s_pop + ".")
    dev = _charge_direct("monnaie").get(ne)          # « monnaie » = devise MONÉTAIRE (yen, naira…) ; PAS `devise_pays`
    if dev:                                          # (qui est le motto national : « Liberté, Égalité, Fraternité »)
        phrases.append("Sa monnaie est %s." % str(dev[1]).lower())
    if len(phrases) < 2:
        return None                          # trop peu de matière -> laisse la voie normale
    return " ".join(phrases)


# FICHE PERSONNE : « parle-moi de Napoléon Ier », « qui est/était X » -> naissance/décès (année + lieu),
# nationalité, occupation, assemblés par lookup STREAMING (RAM-plat sur les fichiers de 100-200 Mo). Nouveau : le
# portrait pays ne couvre que les pays. FAUX=0 : uniquement des faits stockés ; gate = ≥2 attributs de personne.
_PORTRAIT_QUI_RE = re.compile(
    r"^\s*qui\s+(?:est|était|etait|a\s+été|a\s+ete)\s+(?:le\s+|la\s+|l['’])?(.+?)\s*\??\s*$", re.I)


def _cap_portrait_personne(texte: str):
    """FICHE PERSONNE : « qui est Napoléon Ier ? » / « parle-moi de Marie Curie » -> phrase assemblant les faits
    vérifiés (né(e) en ANNÉE à LIEU, mort(e) en ANNÉE à LIEU, nationalité, métier). Lookups en STREAMING (RAM-plat).
    FAUX=0 : rien que des faits stockés ; gate = au moins 2 attributs -> évite de « portraitiser » un non-humain."""
    m = _PORTRAIT_RE.match(texte) or _PORTRAIT_QUI_RE.match(texte)
    if not m:
        return None
    ent = _strip_article(m.group(1).strip())
    if not ent or len(ent) < 3 or len(ent.split()) > 6:
        return None
    if _charge_direct("continent").get(_normalise(ent)):     # un PAYS -> laissé au portrait pays
        return None
    # COURT-CIRCUIT perf : les 6 lookups scannent chacun un fichier de 100-200 Mo (~0,4 s). Pour un NON-personne
    # (« qui est le président … »), on éviterait 6 scans. On sonde d'abord naissance PUIS décès ; si les DEUX
    # manquent, l'entité n'est pas une personne documentée -> abandon après 2 scans (au lieu de 6). Presque toutes
    # les personnes ont une année de naissance ou de décès.
    naiss = _lookup_cell("annee_naissance_personne", ent)
    deces = _lookup_cell("annee_deces_personne", ent)
    if not naiss and not deces:
        return None
    lieu_n = _lookup_cell("lieu_naissance", ent)
    lieu_d = _lookup_cell("lieu_deces", ent)
    natio = _lookup_cell("nationalite_personne", ent)
    occ = _lookup_cell("occupation_personne", ent)
    faits = [x for x in (naiss, deces, lieu_n, lieu_d, natio, occ) if x]
    if len(faits) < 2:                                       # pas assez -> pas une personne connue ici
        return None
    aff = (naiss or deces or lieu_n or lieu_d or natio or occ)[0]   # forme d'affichage stockée
    sujet = aff[:1].upper() + aff[1:]
    sexe = _lookup_cell("sexe_personne", ent)               # accord né/née, mort/morte (streaming, RAM-plat)
    fem = bool(sexe) and "femin" in _normalise(str(sexe[1]))   # needle SANS accent (la chaîne est normalisée)
    ne_e, mort_e = ("née", "morte") if fem else ("né", "mort")
    bornes = lambda a: ("%s av. J.-C." % -int(a)) if str(a).lstrip("-").isdigit() and int(a) < 0 else str(a)
    # nationalite_personne stocke le PAYS (« France ») -> on le présente tel quel (« originaire de France »)
    natio_txt = ("originaire de %s" % natio[1]) if natio else ""
    if occ:
        # vivant (pas d'année de décès) -> PRÉSENT : « Messi était footballeur » implique un décès (faux) ;
        # sexe connu -> forme accordée du libellé inclusif Wikidata (« footballeur ou footballeuse »)
        occ_txt = str(occ[1]).lower()
        if sexe:
            occ_txt = _occupation_selon_genre(occ_txt, fem)
        tete = "%s %s %s" % (sujet, "était" if deces else "est", occ_txt)
        if natio_txt:
            tete += ", %s" % natio_txt
    elif natio_txt:
        tete = "%s, %s" % (sujet, natio_txt)
    else:
        tete = sujet
    seg_n = seg_d = ""
    if naiss:
        seg_n = "%s en %s" % (ne_e, bornes(naiss[1])) + (" à %s" % lieu_n[1] if lieu_n else "")
    elif lieu_n:
        seg_n = "%s à %s" % (ne_e, lieu_n[1])
    if deces:
        seg_d = "%s en %s" % (mort_e, bornes(deces[1])) + (" à %s" % lieu_d[1] if lieu_d else "")
    elif lieu_d:
        seg_d = "%s à %s" % (mort_e, lieu_d[1])
    bio = ", ".join(s for s in (seg_n, seg_d) if s)
    return tete + ("." if not bio else " (%s)." % bio)


# FAIT CIBLÉ sur une PERSONNE (un seul attribut) : « où est né X », « de quelle nationalité est X », « quel métier
# faisait X », « quand est mort X ». Lookup STREAMING (RAM-plat) -> rapide sans le moteur lourd. FAUX=0 : fait stocké.
# (intitulé de l'intention, relation, gabarit d'affichage). L'ordre compte : « où est né » avant « quand est né ».
_FAIT_PERSONNE_RULES = (
    (re.compile(r"^\s*o[ùu]\s+(?:est|était|etait)\s+n[ée]e?\s+(.+?)\s*\??\s*$", re.I),
     "lieu_naissance", "%s est né%s à %s"),
    (re.compile(r"^\s*o[ùu]\s+(?:est|était|etait)\s+mort\w*\s+(.+?)\s*\??\s*$", re.I),
     "lieu_deces", "%s est mort%s à %s"),
    (re.compile(r"^\s*(?:en\s+quelle\s+ann[ée]+e?\s+|quand\s+)(?:est|était|etait)\s+n[ée]e?\s+(.+?)\s*\??\s*$", re.I),
     "annee_naissance_personne", "%s est né%s en %s"),
    (re.compile(r"^\s*(?:en\s+quelle\s+ann[ée]+e?\s+|quand\s+)(?:est|était|etait)\s+mort\w*\s+(.+?)\s*\??\s*$", re.I),
     "annee_deces_personne", "%s est mort%s en %s"),
    (re.compile(r"^\s*(?:de\s+quelle\s+nationalit[ée]\s+(?:est|était|etait)\s+|quelle\s+(?:est|était|etait)\s+la\s+"
                r"nationalit[ée]\s+d[eu'’]\s*)(.+?)\s*\??\s*$", re.I),
     "nationalite_personne", "%s était originaire de %s"),
    (re.compile(r"^\s*(?:quel\s+(?:m[ée]tier|profession)\s+(?:faisait|avait|exer[çc]ait)\s+|que\s+faisait\s+"
                r"|quel\s+(?:est|était|etait)\s+(?:le\s+|son\s+)?m[ée]tier\s+d[eu'’]\s*"
                r"|quelle\s+(?:est|était|etait)\s+(?:la\s+|l['’])?(?:profession|occupation|activit[ée])\s+d[eu'’]\s*)"
                r"(.+?)\s*\??\s*$", re.I),
     "occupation_personne", "%s était %s"),
)


# COMPARAISON DE NAISSANCE entre deux personnes : « qui est né avant, X ou Y ? », « qui est le plus âgé entre X
# et Y ? ». Compare les ANNÉES DE NAISSANCE (précis, pas les dates de règne). FAUX=0 : deux dates vérifiées.
_NAISS_CMP_RE = re.compile(
    r"^\s*(?:qui\s+est\s+né[e]?\s+(avant|apr[èe]s|le\s+premier|en\s+premier)"
    r"|qui\s+est\s+le\s+plus\s+(âgé|age|vieux|vieille|jeune|ancien)"
    r"|lequel\s+est\s+le\s+plus\s+(âgé|age|vieux|jeune))\b[^?]*?"
    r"(?:entre\s+|,\s*)?(.+?)\s+(?:et|ou)\s+(.+?)\s*\??\s*$", re.I)


def _cap_naissance_compare(texte: str):
    """QUI EST NÉ AVANT / LE PLUS ÂGÉ entre deux personnes : compare les années de NAISSANCE (précis). « qui est
    le plus âgé entre Napoléon Ier et Louis XIV ? » -> Louis XIV (1638 < 1769). FAUX=0 : deux dates vérifiées ou
    None ; « plus jeune » inverse. Distinct de _cap_temporel (qui prendrait une date de règne, imprécise)."""
    m = _NAISS_CMP_RE.match(texte.strip())
    if not m:
        return None
    critere = _normalise(next((g for g in m.groups()[:3] if g), ""))
    gx = re.sub(r"^(?:entre|parmi)\s+", "", m.group(4).strip(), flags=re.I)   # « entre » parfois avalé dans x
    x, y = _strip_article(gx), _strip_article(m.group(5).strip())
    if not x or not y or len(x.split()) > 5 or len(y.split()) > 5:
        return None
    cx = _lookup_cell("annee_naissance_personne", x)
    cy = _lookup_cell("annee_naissance_personne", y)
    if not cx or not cy:
        return None
    ax, ay = _nombre(cx[1]), _nombre(cy[1])
    if ax is None or ay is None:
        return None
    ax, ay = int(ax), int(ay)
    veut_jeune = ("jeune" in critere or "apres" in critere)   # le plus jeune = né le PLUS TARD
    borne = lambda a: ("%d av. J.-C." % -a) if a < 0 else "%d" % a
    if ax == ay:
        return "%s et %s sont nés la même année (%s)." % (cx[0], cy[0], borne(ax))
    plus_tot = (ax < ay)
    gagne = (cx, ax) if (plus_tot != veut_jeune) else (cy, ay)
    perd = (cy, ay) if (plus_tot != veut_jeune) else (cx, ax)
    qualif = "le plus jeune" if veut_jeune else "le plus âgé"
    return "%s — %s (né en %s), contre %s (né en %s)." % (gagne[0][0], qualif, borne(gagne[1]),
                                                          perd[0][0], borne(perd[1]))


# SUCCESSION : « qui a succédé à Louis XIV ? » -> son successeur ; « qui a précédé X / prédécesseur de X ? » ->
# son prédécesseur. Relations predecesseur_personne / successeur_personne (personne -> personne). FAUX=0 : fait réel.
_SUCCESSION_RULES = (
    (re.compile(r"^\s*(?:qui\s+a\s+succéd[ée]\s+[àa]\s+|qui\s+(?:est|était|etait)\s+(?:le\s+|la\s+|l['’])?"
                r"successeur\s+d[eu'’]\s*|par\s+qui\s+(.+?)\s+a[- ]t[- ](?:il|elle)\s+[ée]t[ée]\s+remplac[ée]e?)"
                r"(.*?)\s*\??\s*$", re.I), "successeur_personne", "%s a succédé à %s"),
    (re.compile(r"^\s*(?:qui\s+a\s+préc[ée]d[ée]\s+|qui\s+(?:est|était|etait)\s+(?:le\s+|la\s+|l['’])?"
                r"préd[ée]cesseur\s+d[eu'’]\s*)(.+?)\s*\??\s*$", re.I), "predecesseur_personne", "%s a précédé %s"),
)


def _cap_succession(texte: str):
    """SUCCESSION dynastique/de fonction : « qui a succédé à Louis XIV ? » -> Louis XV ; « qui a précédé Louis XIV ? »
    -> Louis XIII. Relations predecesseur/successeur_personne. FAUX=0 : personne réellement stockée, None sinon."""
    for patron, rel, gabarit in _SUCCESSION_RULES:
        m = patron.match(texte.strip())
        if not m:
            continue
        # certaines formes ont 2 groupes (« par qui X a-t-il été remplacé ») : on prend le 1er non vide
        ent = next((g for g in m.groups() if g), "")
        ent = _strip_article(ent.strip())
        if not ent or len(ent) < 3 or len(ent.split()) > 6:
            return None
        cell = _lookup_cell(rel, ent)
        if not cell or cell[1] in (None, ""):
            return None
        # gabarit « <valeur> a succédé à <entité> » (le successeur stocké a succédé à l'entité demandée)
        return (gabarit % (cell[1], cell[0])) + "."
    return None


# CRÉATEUR d'une œuvre : « qui a écrit 1984 ? » -> George Orwell. Le VERBE désigne la famille de relations
# (auteur_*, compositeur_*, realisateur_*, architecte_*, inventeur_*, peintre_*). Via _lookup_direct (streaming,
# valeur UNIQUE dans la famille). FAUX=0 : créateur réellement stocké ou None. Léger (avant le moteur lourd).
_CREATEUR_RULES = (
    (re.compile(r"^\s*(?:qui\s+a\s+(?:[ée]crit?|r[ée]dig[ée]|pondu)|qui\s+est\s+l['’]auteur\s+d[eu'’]|"
                r"de\s+qui\s+est\s+le\s+(?:livre|roman))\s+"
                r"(.+?)\s*\??\s*$", re.I), "auteur", "%s a été écrit par %s"),
    (re.compile(r"^\s*(?:qui\s+a\s+compos[ée]+|qui\s+est\s+le\s+compositeur\s+d[eu'’])\s+(.+?)\s*\??\s*$", re.I),
     "compositeur", "%s a été composé par %s"),
    (re.compile(r"^\s*(?:qui\s+a\s+(?:r[ée]alis[ée]|tourn[ée])|qui\s+est\s+le\s+r[ée]alisateur\s+d[eu'’])\s+"
                r"(.+?)\s*\??\s*$", re.I),
     "realisateur", "%s a été réalisé par %s"),
    (re.compile(r"^\s*(?:qui\s+a\s+peint|qui\s+est\s+le\s+peintre\s+d[eu'’])\s+(.+?)\s*\??\s*$", re.I),
     "peintre", "%s a été peint par %s"),
    (re.compile(r"^\s*(?:qui\s+a\s+(?:conçu|construit|bâti|bati|dessin[ée])|qui\s+est\s+l['’]architecte\s+d[eu'’])\s+"
                r"(.+?)\s*\??\s*$", re.I), "architecte", "%s a été conçu par %s"),
    (re.compile(r"^\s*(?:qui\s+a\s+invent[ée]|qui\s+est\s+l['’]inventeur\s+d[eu'’])\s+(.+?)\s*\??\s*$", re.I),
     "inventeur", "%s a été inventé par %s"),
    (re.compile(r"^\s*(?:qui\s+a\s+d[ée]couvert|qui\s+est\s+le\s+d[ée]couvreur\s+d[eu'’])\s+(.+?)\s*\??\s*$", re.I),
     "auteur_decouverte", "%s a été découvert par %s"),
)

# CRÉATEUR SANS MÉDIA NOMMÉ : « de qui est la Joconde ? », « qui a fait Guernica ? » — la famille est inconnue,
# on les essaie toutes (auteur, peintre, compositeur, réalisateur, sculpteur) dans _cap_createur.
_CREATEUR_GENERIQUE_RE = re.compile(
    r"^\s*(?:de\s+qui\s+est|qui\s+a\s+(?:fait|créé|cree))\s+(.+?)\s*\??\s*$", re.I)

# VÉRIFICATION créateur : « est-ce qu'Orwell a écrit 1984 ? », « c'est bien Orwell qui a écrit 1984 ? » ->
# Oui/Non VÉRIFIÉ (le « Non » est sound : le vrai créateur est donné). Marqueur de confirmation OBLIGATOIRE.
_VERIF_CREATEUR_RE = re.compile(
    r"^\s*(?:est[- ]?ce\s+qu[e'’]\s*|c['’] ?est\s+bien\s+)(.+?)\s+(?:qui\s+)?a\s+"
    r"(écrit|composé|peint|réalisé|tourné)\s+(.+?)\s*\??\s*$", re.I)
_PART_FAMILLE = {"écrit": "auteur", "composé": "compositeur", "peint": "peintre",
                 "réalisé": "realisateur", "tourné": "realisateur"}


def _cap_verif_createur(texte: str):
    """Confirme/réfute une attribution d'œuvre : « c'est bien Orwell qui a écrit 1984 ? » -> « Oui — 1984 a été
    écrit par George Orwell. » FAUX=0 : le verdict vient du fait vérifié (nom complet OU nom de famille exact) ;
    le « Non » donne le vrai créateur (fait vérifié) ; None si le fait manque."""
    m = _VERIF_CREATEUR_RE.match(texte.strip())
    if not m:
        return None
    qui, part, brut = m.group(1).strip(), m.group(2).lower(), m.group(3).strip().strip(" ?.!\"'«»")
    head = _PART_FAMILLE.get(part)
    ent = _strip_article(brut)
    if not head or not ent or len(ent) < 2 or len(qui.split()) > 5:
        return None
    val = None
    for forme in dict.fromkeys((brut, ent)):
        val = _lookup_direct(head, forme)
        if val is not None and str(val).strip():
            break
    if val is None or str(val).strip() == "":
        return None
    nq, nv = _normalise(_strip_article(qui)), _normalise(str(val))
    aff = brut[:1].upper() + brut[1:]
    fem = "e" if brut.lower().startswith("la ") else ""
    if nq == nv or nv.endswith(" " + nq):             # nom complet OU nom de famille (« Orwell » ⊂ « George Orwell »)
        return "Oui — %s a été %s%s par %s." % (aff, part, fem, val)
    return "Non — c'est %s qui a %s %s." % (val, part, brut)


# ŒUVRES d'un créateur (reverse) : « qu'a écrit George Orwell ? » -> ses livres. On cherche dans la FAMILLE de
# relations du verbe (auteur_*, compositeur_*…) les entités dont la valeur = la personne. FAUX=0 : œuvres réelles.
_OEUVRES_RE = re.compile(
    r"^\s*(?:qu['’]?\s*a[- ]t[- ](?:il|elle)\s+(écrit|compos[ée]|r[ée]alis[ée]|peint|invent[ée])"
    r"|qu['’]?\s*a\s+(écrit|compos[ée]|r[ée]alis[ée]|peint|invent[ée])"
    r"|quelles?\s+(?:sont\s+les\s+)?(?:œuvres|oeuvres|livres|romans|tableaux|films|compositions)\s+"
    r"(?:a[- ]t[- ](?:il|elle)\s+(?:écrit|compos[ée]|r[ée]alis[ée])\s+|d[eu'’]\s*|écrit\w*\s+par\s+))\s*(.+?)\s*\??\s*$",
    re.I)
_OEUVRES_VERBE_HEAD = {"ecrit": "auteur", "compose": "compositeur", "composee": "compositeur",
                       "realise": "realisateur", "realisee": "realisateur", "peint": "peintre",
                       "invente": "inventeur", "inventee": "inventeur"}


def _reverse_famille(head: str, valeur: str, limite: int = 15):
    """Entités dont la VALEUR = `valeur` dans toutes les relations dont la tête = `head` (auteur_livre, auteur_bd…).
    Union, sans doublon, triée. Utilise _charge_reverse (garde 64 Mo). Pour « les œuvres DE <personne> »."""
    nv = _normalise(valeur)
    trouve, nom_retenu = [], None
    for rel in _relations():
        if rel.split("_")[0] != head:
            continue
        idx = _charge_reverse(rel)
        hit = idx.get(nv)
        if hit is None and len(nv) >= 4 and " " not in nv:
            # NOM DE FAMILLE seul (« Orwell » alors que la base dit « George Orwell ») : suffixe UNIQUE exigé
            # dans la relation ET cohérent entre relations — deux personnes distinctes -> abstention (FAUX=0).
            cles = [k for k in idx if k.endswith(" " + nv)]
            noms = {idx[k][0] for k in cles}
            if len(noms) != 1:
                continue
            nom = next(iter(noms))
            if nom_retenu and _normalise(nom_retenu) != _normalise(nom):
                return []
            nom_retenu = nom
            hit = (nom, sorted({e for k in cles for e in idx[k][1]}))
        if hit and hit[1]:
            for e in hit[1]:
                if e not in trouve:
                    trouve.append(e)
        if len(trouve) >= limite * 2:
            break
    return sorted(trouve)[:limite]


def _cap_oeuvres_de(texte: str):
    """ŒUVRES d'un créateur : « qu'a écrit George Orwell ? » / « quelles œuvres de Proust ? » -> la liste. Reverse
    sur la famille du verbe. FAUX=0 : œuvres réellement attribuées, ou None. Léger."""
    m = _OEUVRES_RE.match(texte.strip())
    if not m:
        return None
    verbe = next((g for g in m.groups()[:-1] if g), None)
    pers = _strip_article(m.group(m.lastindex).strip())
    if not pers or len(pers) < 3:
        return None
    # verbe absent (« quelles œuvres de Proust ») -> on tente toutes les familles créatives
    heads = [_OEUVRES_VERBE_HEAD[_normalise(verbe)]] if verbe else ["auteur", "compositeur", "realisateur", "peintre"]
    oeuvres = []
    for h in heads:
        oeuvres = _reverse_famille(h, pers)
        if oeuvres:
            break
    if not oeuvres:
        return None
    aff = ", ".join(o for o in oeuvres)
    suite = " …" if len(oeuvres) >= 15 else ""
    return "%s : %s%s." % (pers[:1].upper() + pers[1:], aff, suite)


# TYPE-WORD d'œuvre en tête d'un titre (« le film Pulp Fiction », « le roman 1984 ») : la clé réelle des
# datasets est le titre NU — le type est jeté avant lookup (liste fermée de médias).
_TYPE_OEUVRE_RE = re.compile(
    r"^(?:le\s+film|le\s+livre|le\s+bouquin|le\s+roman|le\s+tableau|la\s+peinture|la\s+toile|la\s+statue|la\s+sculpture|"
    r"la\s+chanson|la\s+s[ée]rie|le\s+jeu(?:\s+vid[ée]o)?|l['’]\s*album|le\s+morceau|l['’]\s*op[ée]ra|"
    r"la\s+pi[eè]ce(?:\s+de\s+th[ée][âa]tre)?|le\s+po[eè]me|la\s+bd|la\s+bande\s+dessin[ée]e)\s+", re.I)


def _cap_createur(texte: str):
    """CRÉATEUR d'une œuvre : « qui a écrit 1984 ? » -> George Orwell ; « qui a composé le Boléro ? » -> Ravel ;
    « qui a réalisé Titanic ? » -> Cameron. Via _lookup_direct sur la famille du verbe. FAUX=0 : valeur UNIQUE
    stockée ou None. Léger (sans moteur lourd)."""
    for patron, head, gabarit in _CREATEUR_RULES:
        m = patron.match(texte.strip())
        if not m:
            continue
        brut = m.group(1).strip().strip(" ?.!\"'«»")     # forme AVEC article (certains titres sont stockés ainsi)
        ent = _strip_article(brut)
        if not ent or len(ent) < 2:
            return None
        # TYPE-WORD d'œuvre jeté (« le film Pulp Fiction » -> « Pulp Fiction » : la clé réelle n'a pas le type)
        sans_type = _TYPE_OEUVRE_RE.sub("", brut).strip()
        affiche = val = None
        for forme in dict.fromkeys((ent, brut, sans_type, _strip_article(sans_type))):
            if not forme or len(forme) < 2:
                continue
            fam = _lookup_famille(head, forme)           # « la joconde » clé réelle ; variantes d'article gérées
            vals = list(dict.fromkeys(str(c[2]) for c in fam if str(c[2]).strip()))
            if len(vals) == 1:
                affiche, val = (fam[0][1] or forme), vals[0]   # forme STOCKÉE (« La Joconde » -> accord peintE)
                break
            if len(vals) >= 2:
                # HOMONYMIE d'œuvres (« la Neuvième Symphonie » : œuvre de Beethoven ET film dont Kurt Schröder
                # a composé la musique) : on LISTE les sens vérifiés au lieu d'abstenir en silence — FAUX=0.
                lignes = "\n".join("· %s (%s)" % (c[2], c[0].replace("_", " ")) for c in fam[:4])
                return "Plusieurs œuvres homonymes portent ce nom — voici ce que j'ai de vérifié :\n%s" % lignes
        if val is None:
            return None
        if affiche.lower().startswith("la "):            # accord du participe (« La Joconde a été peintE par »)
            gabarit = gabarit.replace(" par ", "e par ", 1)
        return (gabarit % (affiche[:1].upper() + affiche[1:], val)) + "."
    # CRÉATEUR GÉNÉRIQUE (« de qui est X ? », « qui a fait/créé X ? ») : le média n'est pas nommé -> on essaie
    # les familles créatives dans l'ordre. FAUX=0 : premier fait vérifié trouvé, sinon None.
    mg = _CREATEUR_GENERIQUE_RE.match(texte.strip())
    if mg:
        brut = mg.group(1).strip().strip(" ?.!\"'«»")
        ent = _strip_article(brut)
        sans_type = _TYPE_OEUVRE_RE.sub("", brut).strip()
        if ent and len(ent) >= 2:
            trouves = []                                     # (forme, participe, créateur) — TOUS les sens vérifiés
            for head, part in (("auteur", "écrit"), ("peintre", "peint"), ("compositeur", "composé"),
                               ("realisateur", "réalisé"), ("sculpteur", "sculpté")):
                for forme in dict.fromkeys((brut, ent, sans_type, _strip_article(sans_type))):   # article d'abord
                    val = _lookup_direct(head, forme)
                    if val is not None and str(val).strip() and all(v != val for _f, _p, v in trouves):
                        trouves.append((forme, part, val))
                        break
            if len(trouves) == 1:
                forme, part, val = trouves[0]
                fem = "e" if forme.lower().startswith("la ") else ""
                return "%s a été %s%s par %s." % (forme[:1].upper() + forme[1:], part, fem, val)
            if len(trouves) >= 2:
                # HOMONYMIE d'œuvres (« Joconde » = tableau de Vinci ET conte de La Fontaine) : on LISTE les
                # sens vérifiés au lieu d'en choisir un au hasard — FAUX=0 exige de ne pas trancher sans fait.
                lignes = "\n".join("· %s%s par %s" % (p, "e" if f.lower().startswith("la ") else "", v)
                                   for f, p, v in trouves)
                return "Plusieurs œuvres portent ce nom — voici ce que j'ai de vérifié :\n%s" % lignes
    return None


def _occupation_selon_genre(val: str, fem: bool) -> str:
    """Les libellés P106 de Wikidata sont INCLUSIFS (« footballeur ou footballeuse ») : quand le sexe de la
    personne est CONNU, on garde la forme accordée (masc = 1ʳᵉ, fém = 2ᵉ) — transformation de libellé
    déterministe, pas une invention. Composants d'une jointure traités un à un ; sans « ou », inchangé."""
    def _forme(part: str) -> str:
        if " ou " in part:
            g, d = part.split(" ou ", 1)
            return d.strip() if fem else g.strip()
        return part
    morceaux = val.split(" et ")
    morceaux = [", ".join(_forme(p) for p in m.split(", ")) for m in morceaux]
    return " et ".join(morceaux)


def _cap_fait_personne(texte: str):
    """FAIT CIBLÉ sur une personne (lieu/année de naissance ou décès, nationalité, métier) via lookup STREAMING —
    « où est né Napoléon Ier ? » -> « Napoléon Ier est né à Ajaccio. ». FAUX=0 : fait stocké réel, None sinon ;
    accord en genre via sexe_personne. Rapide (pas de moteur lourd)."""
    for patron, rel, gabarit in _FAIT_PERSONNE_RULES:
        m = patron.match(texte.strip())
        if not m:
            continue
        ent = _strip_article(m.group(1).strip())
        if not ent or len(ent) < 3 or len(ent.split()) > 6:
            return None
        if _charge_direct("continent").get(_normalise(ent)):       # pas un pays
            return None
        cell = _lookup_cell(rel, ent)
        if not cell or cell[1] in (None, ""):
            return None
        aff, val = cell[0], str(cell[1])
        if rel.startswith("annee_"):                               # date -> gérer av. J.-C.
            val = ("%s av. J.-C." % -int(val)) if val.lstrip("-").isdigit() and int(val) < 0 else val
        if "né%s" in gabarit or "mort%s" in gabarit:               # accord en genre
            sexe = _lookup_cell("sexe_personne", ent)
            e = "e" if (sexe and "femin" in _normalise(str(sexe[1]))) else ""
            return (gabarit % (aff[:1].upper() + aff[1:], e, val)) + "."
        if rel == "occupation_personne":
            val = val.lower()
            sexe = _lookup_cell("sexe_personne", ent)
            if sexe:                                               # sexe connu -> forme accordée du libellé inclusif
                val = _occupation_selon_genre(val, "femin" in _normalise(str(sexe[1])))
        if "était" in gabarit and not _lookup_cell("annee_deces_personne", ent):
            gabarit = gabarit.replace("était", "est")              # vivant -> présent (« était » implique un décès)
        return (gabarit % (aff[:1].upper() + aff[1:], val)) + "."
    return None


# LOCALISATION d'un lieu : « où se trouve X », « dans quel pays est X », « sur quel continent est X ». On cherche
# X dans les relations géo pays_*/continent_* (montagne/désert/île/lac/rivière/fleuve/ville). FAUX=0 : valeur réelle.
_LOC_PAYS_REL = ("pays_montagne", "pays_desert", "pays_ile", "pays_lac", "pays_riviere", "pays_fleuve",
                 "pays_ville", "pays_massif", "pays_volcan", "pays_chute_eau")
_LOC_CONT_REL = ("continent", "continent_montagne", "continent_desert", "continent_ile", "continent_lac",
                 "continent_riviere", "continent_fleuve")
_LOC_PAYS_RE = re.compile(
    r"^\s*(?:dans\s+|de\s+)?quel\s+pays\s+(?:est|se\s+(?:trouve|situe)|coule|se\s+jette|est\s+situ[ée]e?|"
    r"fait[- ](?:il|elle)\s+partie|abrite[-]t[-](?:il|elle))?\s*(?:la\s+|le\s+|les\s+|l['’]|du\s+|des\s+|de\s+)?"
    r"(.+?)\s*\??\s*$", re.I)
_LOC_CONT_RE = re.compile(
    r"^\s*(?:sur|dans)\s+quel\s+continent\s+(?:est|se\s+(?:trouve|situe)|est\s+situ[ée]e?)?\s*"
    r"(?:la\s+|le\s+|les\s+|l['’]|du\s+|des\s+|de\s+)?(.+?)\s*\??\s*$", re.I)
_LOC_OU_RE = re.compile(
    r"^\s*o[ùu]\s+(?:se\s+(?:trouve|situe)|est\s+(?:situ[ée]e?)?)\s+"
    r"(?:la\s+|le\s+|les\s+|l['’]|du\s+|des\s+|de\s+)?(.+?)\s*\??\s*$", re.I)


def _est_concept_commun(ent: str) -> bool:
    """L'entité est-elle un NOM COMMUN abstrait (le bonheur, l'amour…) plutôt qu'un lieu ? Un mot UNIQUE tagué « nom »
    (commun) dans le lexique POS — PAS « nom propre » — est probablement un concept, pas un toponyme. Évite « où se
    trouve le bonheur ? » -> un hameau nommé « Bonheur » (faux-ami). FAUX=0 : on s'abstient plutôt que de mal viser."""
    if len(ent.split()) != 1:
        return False
    try:
        import est_un as _E
        return _E._pos().get(_normalise(ent)) == "nom"
    except Exception:
        return False


# Segments d'une question à ordre libre : on découpe sur les virgules / « : » et on cherche la TÊTE DE RELATION
# d'un côté, l'ENTITÉ de l'autre — quel que soit l'ordre. Mots à ignorer (bruit d'énoncé).
_SVO_BRUIT = frozenset(
    "dis dites moi nous quel quelle quels quelles est sont ce c qu quoi la le les un une de du des au aux "
    "en et pour avec sur dans son sa ses leur leurs mon ma mes ton ta tes alors donc sinon franchement "
    "stp svp merci s'il te vous plait connais sais peux pourrais eh bah ben ah oh".split())


# Relations-sonde à clés PROPRES (pays, villes, personnes) pour tester si un mot est une entité NOMMÉE. On EXCLUT
# definition_nom : un NOM COMMUN y est défini aussi (« capitale », « monnaie » = ville/moyen de paiement) et ne
# doit PAS compter comme entité — sinon le garde bloque une reformulation légitime « chef-lieu -> capitale ».
_SONDE_PROPRE = ("capitale", "continent", "monnaie", "population_pays", "superficie", "annee_naissance_personne")


def _est_entite_probable(mot: str) -> bool:
    """`mot` (normalisé) désigne-t-il probablement une ENTITÉ NOMMÉE (nom propre) ? Deux signaux OFFLINE : le POS
    le tague « nom propre » (france, japon) OU il est la CLÉ d'un fait dans une relation à clés propres (pays/
    ville/personne — PAS definition_nom, qui définit aussi les noms communs). FAUX=0 : empêche un alias appris
    d'échanger un SUJET, sans bloquer une reformulation de mot commun (« chef-lieu » -> « capitale »)."""
    try:
        import est_un as _E
        if _E._pos().get(mot) == "nom propre":
            return True
    except Exception:
        pass
    for rel in _SONDE_PROPRE:
        try:
            cell = _lookup_cell(rel, mot)
        except Exception:
            cell = None
        if cell and cell[1] is not None:
            return True
    return False


def _alias_change_entite(orig: str, alias: str) -> bool:
    """True si l'alias appris ÉCHANGE le SUJET en INJECTANT une entité (nom propre / fait ancré) absente de la
    question d'origine (« population du WAKANDA » -> « … du FRANCE » injecte « france » -> réponse sur la France,
    FAUX). On ne regarde QUE les mots INTRODUITS : le danger est de répondre sur une entité NON demandée ; un mot
    simplement RETIRÉ (« koi » -> « quoi ») ne fabrique pas de faux (le lookup d'un sujet manquant ne trouve rien).
    FAUX=0 : un patron corrige une FORMULATION, jamais de quoi on parle. Mots de contenu ≥3."""
    mots_orig = set(re.findall(r"[\wà-ÿ]{3,}", _normalise(orig)))
    for mot in set(re.findall(r"[\wà-ÿ]{3,}", _normalise(alias))) - mots_orig:
        if mot not in _NEST_SCAFFOLD and mot not in _GENERIQUES and _est_entite_probable(mot):
            return True
    return False


def _parse_svo_libre(texte: str, conv_id: str | None = None):
    """DERNIER RECOURS de compréhension OUVERTE : aucune règle n'a matché, mais la question contient une TÊTE DE
    RELATION connue (_attr_heads) et une ENTITÉ ancrable, dans un ordre LIBRE (« du Japon, dis-moi la capitale »,
    « la capitale, pour le Japon ? », « Japon : monnaie ? »). On isole (tête, entité) sans se soucier de l'ordre,
    on reconstruit la forme canonique « <tête> de <entité> » et on la REJOUE en lookup vérifié. FAUX=0 absolu :
    on ne renvoie QUE si le fait se vérifie ; sinon None (l'abstention structurée prend le relais). Renvoie
    (réponse, tête, entité) ou None."""
    heads = _attr_heads()
    # segments = tranches séparées par virgules / deux-points / « pour ». On découpe le texte BRUT puis on
    # normalise CHAQUE segment (crucial : _normalise supprime les virgules, découper après = un seul bloc).
    segments = [_normalise(s).strip() for s in re.split(r"\s*[,:]\s*|\s+pour\s+", texte.strip(" ?.!"))
                if _normalise(s).strip()]
    if len(segments) < 2:                          # l'ordre libre a besoin d'au moins 2 blocs (relation | entité)
        return None
    # TÊTE = un segment (ou son 1er mot de contenu) qui est une tête de relation connue.
    tete = None
    reste = []
    for seg in segments:
        mots = [w for w in seg.split() if w not in _SVO_BRUIT]
        cand = next((w for w in mots if w in heads), None)
        if cand and tete is None:
            tete = cand
            autres = [w for w in mots if w != cand]
            if autres:                             # « la monnaie qu'on utilise » : contenu résiduel = pas l'entité
                reste.append(" ".join(autres))
        else:
            reste.append(seg)
    if not tete or not reste:
        return None
    # ENTITÉ = le plus long segment résiduel qui s'ANCRE (fait vérifié via la sonde) — jamais un concept commun.
    cand_ents = sorted((s.strip() for s in reste if len(s.strip()) >= 2), key=len, reverse=True)
    for ent in cand_ents:
        ent = _strip_article(ent)
        if not ent or len(ent.split()) > 5 or _est_concept_commun(ent) or _normalise(ent) in heads:
            continue
        rep = _connaissance_verifiee("%s de %s" % (tete, ent), conv_id)
        if rep and not est_fallback(rep):
            return (rep, tete, ent)
    return None


# ————— RECORDS GÉOGRAPHIQUES MONDIAUX (couche curée, vérifiée LIVE contre les données quand elles existent) —————
# Les argmax MONDE sur les tables brutes seraient FAUX : altitude_montagne contient 37 reliefs MARTIENS/vénusiens
# (Tharsis Tholus 8 930 m > Everest !), longueur_fleuve ne couvre NI le Nil NI l'Amazone, superficie_ile n'a pas
# le Groenland (audit 2026-07-06). Cette table FERMÉE porte les records incontestables ; quand la donnée existe
# (Everest, Sahara, planètes) la valeur est RELUE en direct ; les primautés DISPUTÉES (Nil/Amazone) sont dites
# disputées — jamais tranchées arbitrairement.
_RECORD_ADJS = r"(haute?s?|grande?s?|long(?:ue)?s?|vastes?|profonde?s?)"
_RECORD_TYPES = r"(sommet|montagne|fleuve|rivi[eè]re|[îi]le|d[ée]sert|oc[ée]an|lac|plan[eè]te|fosse)"
_RECORD_MONDE_FIN = r"(?:\s+(?:du\s+monde|au\s+monde|de\s+la\s+plan[eè]te|sur\s+terre|du\s+syst[eè]me\s+solaire))?\s*\??\s*$"
_RECORD_MONDE_RE = re.compile(              # « le plus haut sommet (du monde) »
    r"(?:quel(?:le)?\s+(?:est\s+)?)?(?:la\s+|le\s+|l['’]\s*)?plus\s+" + _RECORD_ADJS + r"\s+"
    + _RECORD_TYPES + _RECORD_MONDE_FIN, re.I)
_RECORD_MONDE_INV_RE = re.compile(          # « quel sommet est le plus haut (du monde) »
    r"quel(?:le)?\s+" + _RECORD_TYPES + r"\s+est\s+(?:la\s+|le\s+|l['’]\s*)?plus\s+"
    + _RECORD_ADJS + _RECORD_MONDE_FIN, re.I)
_RECORD_MONDE_POST_RE = re.compile(         # « le lac le plus profond (du monde) »
    r"(?:la\s+|le\s+|l['’]\s*)" + _RECORD_TYPES + r"\s+(?:la\s+|le\s+)?plus\s+"
    + _RECORD_ADJS + _RECORD_MONDE_FIN, re.I)


def _cap_record_monde(texte: str):
    """RECORDS mondiaux fermés (« le plus haut sommet du monde ? » -> Everest). Voir bloc de commentaire
    ci-dessus : données relues quand présentes, disputes dites disputées, trous de table signalés."""
    t = texte.strip()
    m = _RECORD_MONDE_RE.search(t)
    if m:
        adj, typ = _normalise(m.group(1)), _normalise(m.group(2))
    else:
        m = _RECORD_MONDE_INV_RE.search(t) or _RECORD_MONDE_POST_RE.search(t)
        if not m:
            return None
        typ, adj = _normalise(m.group(1)), _normalise(m.group(2))
    adj = adj.rstrip("es") if adj not in ("vaste", "vastes") else "vaste"   # haute->haut, longue->longu, long->long
    if typ in ("sommet", "montagne") and adj in ("haut", "grand"):
        cell = _lookup_cell("altitude_montagne", "Everest")
        alt = (" — %s m d'altitude, fait vérifié dans mes données" % cell[1]) if cell else ""
        return "L'Everest%s. C'est le plus haut sommet du monde." % alt
    if typ in ("fleuve", "riviere") and adj in ("long", "longu", "grand"):
        nil, ama = _lookup_cell("longueur_fleuve", "Nil"), _lookup_cell("longueur_fleuve", "Amazone")
        km = lambda c: format(int(float(c[1]) // 1000), ",d").replace(",", " ")
        rel = ((" (Mes données — tracé « court » : Nil %s km, Amazone %s km ; les mesures longues de "
                "l'Amazone montent à ≈ 7 000 km.)" % (km(nil), km(ama))) if (nil and ama) else "")
        return ("Le Nil (≈ 6 650 km) ou l'Amazone (6 400 à 7 000 km selon le tracé retenu) : la primauté est "
                "scientifiquement DISPUTÉE — je ne tranche pas.%s" % rel)
    if typ == "ile" and adj in ("grand", "vaste"):
        cg = _lookup_cell("superficie_ile", "Groenland")     # relu en direct (ré-ingestion BestRank 2026-07-06)
        v = (" (%s km², fait vérifié dans mes données)" % format(int(float(cg[1])), ",d").replace(",", " ")) if cg else ""
        return "Le Groenland%s — l'Australie, plus vaste, est comptée comme un continent." % v
    if typ == "desert" and adj in ("grand", "vaste"):
        cell = _lookup_cell("superficie_desert", "Sahara")
        sah = (" (%s km², fait vérifié dans mes données)" % cell[1]) if cell else ""
        return ("L'Antarctique (désert polaire, ≈ 14 millions de km²) si l'on prend la définition scientifique ; "
                "le plus grand désert CHAUD est le Sahara%s." % sah)
    if typ == "ocean" and adj in ("grand", "vaste", "profond"):
        if adj == "profond":
            return "Le Pacifique — il contient la fosse des Mariannes (≈ 10 935 m, le point le plus profond des océans)."
        return "Le Pacifique (≈ 168,7 millions de km², la moitié de l'océan mondial)."
    if typ == "fosse" and adj == "profond":
        return "La fosse des Mariannes (≈ 10 935 m au point Challenger Deep)."
    if typ == "lac":
        if adj == "profond":
            return "Le lac Baïkal (1 642 m) — aussi le plus grand par le VOLUME d'eau douce."
        return ("La mer Caspienne (≈ 371 000 km²) si on la compte comme un lac ; sinon le lac Supérieur "
                "(≈ 82 100 km²).")
    if typ == "planete" and adj in ("grand", "vaste"):
        par = _charge_direct("diametre_moyen_planete")
        if par:
            best = max(par.items(), key=lambda kv: _nombre(kv[1][1]) or 0)
            return ("Jupiter — %s km de diamètre moyen (comparé sur les %d planètes de mes données)."
                    % (best[1][1], len(par))) if _normalise(best[0]) == "jupiter" else None
        return None
    return None


_FV_TYPES = r"(?:fleuve|rivi[eè]re|cours\s+d[e'’]\s*eau)"
_FV_QUEL_RE = re.compile(
    r"quel(?:le)?\s+" + _FV_TYPES +
    r"\s+(?:traverse|arrose|baigne|passe\s+(?:a|à|par|dans)|coule\s+(?:a|à|dans|par))\s+"
    r"(?:la\s+ville\s+d[e'’]\s*)?(.+?)\s*\??\s*$", re.I)
_FV_SUR_RE = re.compile(
    r"sur\s+quel(?:le)?\s+" + _FV_TYPES +
    r"\s+(?:se\s+trouve|se\s+situe|est\s+situ[ée]+|est)\s+(?:la\s+ville\s+d[e'’]\s*)?(.+?)\s*\??\s*$", re.I)
_FV_VILLES_RE = re.compile(
    r"quelles?\s+villes?\s+(?:est|sont)\s+travers[ée]+e?s?\s+par\s+(.+?)\s*\??\s*$"
    r"|quelles?\s+villes?\s+(.+?)\s+traverse(?:[\s-]*t[\s-]+(?:il|elle))?\s*\??\s*$", re.I)
_FV_OUINON_RE = re.compile(
    r"(?:est[- ]ce\s+que\s+)?(.+?)\s+traverse(?:[\s-]*t[\s-]+(?:il|elle))?\s+"
    r"(?:la\s+ville\s+d[e'’]\s*)?(.+?)\s*\??\s*$", re.I)


def _fv_et(items) -> str:
    return items[0] if len(items) == 1 else "%s et %s" % (", ".join(items[:-1]), items[-1])


def _cap_fleuve_ville(texte: str):
    """« quel fleuve traverse Paris ? » -> la Seine. Seed CURÉ fleuve↔ville (src/fleuve_ville_seed.jsonl) : les
    datasets Wikidata n'ont AUCUNE relation ville↔fleuve (l'ancienne réponse était un déversement de 147
    rivières par _liste_inverse, corrigé par le garde ancre≠type). FAUX=0 : une ville du seed est complète pour
    ses fleuves MAJEURS ; un fleuve n'est pas exhaustif (« notamment ») ; une paire inconnue n'est jamais niée
    sèchement (la Bièvre traverse réellement Paris sans être dans le seed)."""
    import fleuve_ville as _FV
    t = texte.strip()
    m = _FV_QUEL_RE.search(t) or _FV_SUR_RE.search(t)
    if m:
        cell = _FV.fleuves_de(_strip_article(m.group(1).strip()))
        if cell:
            v_aff, fls = cell
            if len(fls) == 1:
                return "C'est %s qui traverse %s." % (fls[0], v_aff)
            return "%s est traversée par %s." % (v_aff, _fv_et(fls))
        return None                       # ville hors seed -> abstention honnête (pas de liste hors-sujet)
    m = _FV_VILLES_RE.search(t)
    if m:
        cell = _FV.villes_de(_strip_article((m.group(1) or m.group(2) or "").strip()))
        if cell:
            f_aff, vils = cell
            return "%s traverse notamment %s (liste non exhaustive)." % (f_aff[0].upper() + f_aff[1:], _fv_et(vils))
        return None
    m = _FV_OUINON_RE.search(t)
    if m:                                 # double ancrage exigé : fleuve ET ville connus du seed, sinon None
        fl, ville = _strip_article(m.group(1).strip()), _strip_article(m.group(2).strip())
        cf, cv = _FV.villes_de(fl), _FV.fleuves_de(ville)
        if cf and cv:
            if _FV.traverse(fl, ville):
                return "Oui — %s traverse %s." % (cf[0], cv[0])
            return ("D'après mes données, %s est traversée par %s — je n'ai pas de fait reliant %s à %s."
                    % (cv[0], _fv_et(cv[1]), cf[0], cv[0]))
    return None


_DEVISE_RE = re.compile(
    r"^\s*(?:quelle\s+est\s+)?(?:la\s+)?devise(\s+nationale)?\s+"
    r"(?:de\s+la\s+|de\s+l['’]|du\s+|des\s+|de\s+|d['’])(.+?)\s*\??\s*$", re.I)


def _cap_devise(texte: str):
    """« la devise de la France ? » est AMBIGU : motto national (« Liberté, Égalité, Fraternité »,
    devise_pays) OU monnaie (euro). Les DEUX lectures vérifiées sont servies — « devise NATIONALE » explicite
    -> motto seul. FAUX=0 : motto stocké exigé, sinon None (la voie monnaie existante répond)."""
    m = _DEVISE_RE.match(texte.strip())
    if not m:
        return None
    ent = _strip_article(m.group(2).strip())
    cell = _charge_direct("devise_pays").get(_normalise(ent))
    if not cell:
        return None
    aff, motto = cell
    tete = "La devise nationale de %s : « %s »." % (aff[:1].upper() + aff[1:], motto)
    if m.group(1):                                    # « devise nationale » demandé explicitement -> motto seul
        return tete
    monnaie = None
    try:
        ia, verifie = _charge_ia()
        if ia:
            monnaie = _val_verifiee(ia, verifie, "monnaie de %s" % ent, rel_head="monnaie", entite=ent)
    except Exception:
        monnaie = None
    if monnaie:
        return "%s  (Si tu voulais la MONNAIE : %s.)" % (tete, monnaie)
    return tete


def _cap_localisation(texte: str):
    """LOCALISATION d'un lieu (montagne/désert/île/lac/rivière/ville) : « dans quel pays est X », « sur quel
    continent est X », « où se trouve X » -> pays ou continent stocké. FAUX=0 : valeur réelle vérifiée ou None
    (entité absente des relations géo). « où » générique essaie le PAYS (plus précis) puis le continent."""
    rels = None
    m = _LOC_PAYS_RE.match(texte.strip())
    if m:
        rels, ent = _LOC_PAYS_REL, m.group(1)
    else:
        m = _LOC_CONT_RE.match(texte.strip())
        if m:
            rels, ent = _LOC_CONT_REL, m.group(1)
        else:
            m = _LOC_OU_RE.match(texte.strip())
            if m:
                rels, ent = _LOC_PAYS_REL + _LOC_CONT_REL, m.group(1)   # où : pays d'abord, sinon continent
    if not rels:
        return None
    ent = _strip_article(ent.strip())
    if not ent or len(ent) < 3 or len(ent.split()) > 6:
        return None
    if _est_concept_commun(ent):                         # « où se trouve le bonheur » : nom COMMUN -> pas un lieu
        return None
    cpays = _charge_direct("continent").get(_normalise(ent))
    if cpays:                                            # X est un PAYS -> « où se trouve la France » relève du continent
        try:
            import realisation_fr as _RF
            sujet = _RF.article_pays(cpays[0], majuscule=True)
        except Exception:
            sujet = cpays[0]
        return "%s se trouve en %s." % (sujet, cpays[1])
    for rel in rels:
        cell = _lookup_cell(rel, ent)
        if cell and cell[1]:
            loc = str(cell[1])
            loc_loc = _locatif_pays(loc) if rel.startswith("pays") else "en " + loc   # « au Portugal », « en Afrique »
            return "%s se trouve %s." % (cell[0][:1].upper() + cell[0][1:], loc_loc)
    return None


def _locatif_pays(pays: str) -> str:
    """« en France », « au Portugal », « aux États-Unis », « à Monaco » — préposition locative selon le genre/nombre."""
    try:
        import realisation_fr as _RF
        if _RF.sans_article(pays):
            return "à " + pays
        g = _RF.genre_pays(pays)
        if g == "p":
            return "aux " + pays
        if g == "m" and not _RF._voyelle_initiale(pays):
            return "au " + pays
        return "en " + pays                              # féminin ou voyelle initiale -> « en »
    except Exception:
        return "en " + pays


_CAUSE_RE = re.compile(
    r"\b(?:cause[s]?|provoque\w*|responsable|agent[s]?|declenche\w*|entrain\w*|etiologie|du[e]?\s+a|due\s+a|"
    r"qu['’ ]?est[- ]ce\s+qui\s+(?:cause|provoque|declenche|donne))\b", re.I)
_CAUSE_RELS_CACHE = None


def _relations_cause() -> list:
    """Relations causales de la base (cause_* / agent_*), triées : les plus SPÉCIFIQUES d'abord (le pathogène précis
    avant le type d'agent). Lu une fois."""
    global _CAUSE_RELS_CACHE
    if _CAUSE_RELS_CACHE is None:
        prio = ["agent_pathogene_maladie", "agent_maladie", "cause_type_diabete", "cause_deces"]
        try:
            rels = [f[:-6] for f in os.listdir(_DOSSIER_LECTEUR)
                    if f.endswith(".jsonl") and (f.startswith("cause_") or f.startswith("agent_"))]
        except OSError:
            rels = []
        _CAUSE_RELS_CACHE = [r for r in prio if r in rels] + [r for r in rels if r not in prio]
    return _CAUSE_RELS_CACHE


def _cap_cause(texte: str):
    """« Quelle est la cause de X ? » / « qu'est-ce qui cause/provoque X ? » / « quel est l'agent de X ? » -> cause
    VÉRIFIÉE depuis les relations causales de la base (cause_*/agent_*). Transforme l'abstention « pourquoi » en
    réponse LÀ où la donnée causale existe (maladies surtout). FAUX=0 : fait réel ou None (jamais une cause inventée)."""
    if not _CAUSE_RE.search(_normalise(texte)):
        return None
    ent = _strip_article(_sujet_de(texte))
    if not ent or len(ent) < 3:            # « qu'est-ce qui CAUSE X » : l'entité suit le verbe, sans « de »
        m = re.search(r"\b(?:cause|causent|provoque\w*|declenche\w*|entrain\w*|donne\w*|responsable\s+de)\s+"
                      r"(?:la\s|le\s|les\s|l['’\s]|du\s|des\s|de\s|d['’\s]|un\s|une\s)?(.+?)\s*\??\s*$", texte, re.I)
        ent = _strip_article(m.group(1)) if m else ent
    if not ent or len(ent) < 3:
        return None
    ne = _normalise(ent)
    trouve = []
    for rel in _relations_cause():
        cell = _charge_direct(rel).get(ne)
        if cell and cell[1] is not None:
            trouve.append((rel, cell[1]))
    if not trouve:
        return None
    # le plus SPÉCIFIQUE (1er par priorité) porte la réponse ; on cite le type d'agent en complément s'il diffère
    principal = trouve[0][1]
    complement = next((v for r, v in trouve[1:] if _normalise(v) != _normalise(principal)), None)
    try:
        import realisation_fr as _RF
        de = _RF.de(ent, genre=_RF.genre_maladie(ent))     # « de la grippe », « du paludisme », « de l'amibiase »
    except Exception:
        de = "de l'" + ent if re.match(r"[aeiouyhàâäéèêëîïôöùûü]", _normalise(ent)) else "de " + ent
    if complement:
        return "La cause %s : %s (%s)." % (de, principal, complement)
    return "La cause %s : %s." % (de, principal)


_RE_INVENTION_COMPO = re.compile(
    r"\b(?:invention|inventions|relations?|attributs?)\b.*?\b(?:manqu|composé|compose|dériv|derivab|nouvelle)\w*\b|"
    r"\b(?:que (?:peut[- ]on|pourrait[- ]on)|qu'?est[- ]ce qu'?on peut) (?:dériver|deriver|inventer|composer)\b|"
    r"\bqu'?est[- ]ce qui manque\b", re.I)
_TYPES_COMPO = {"pays": "pays", "element": "elements", "elements": "elements", "élément": "elements",
                "éléments": "elements", "ville": "villes", "villes": "villes", "capitale": "capitales",
                "capitales": "capitales", "astre": "astres", "astres": "astres", "planete": "astres",
                "planète": "astres", "etoile": "astres", "étoile": "astres"}


_RE_TRADUIRE = re.compile(
    r"(?:tradui[stre]+|traduction\s+de|comment\s+(?:dit|dire|on\s+dit)[- ]on|comment\s+se\s+dit|translate)\b"
    r"(.*?)\b(?:en|in|to|vers)\s+(anglais|english|français|francais|french|espagnol|spanish|allemand|german|"
    r"italien|italian|portugais|portuguese)\s*\??\s*$", re.I | re.S)
_CIBLE_TRAD = {"anglais": "en", "english": "en", "français": "fr", "francais": "fr", "french": "fr",
               "espagnol": "es", "spanish": "es", "allemand": "de", "german": "de", "italien": "it",
               "italian": "it", "portugais": "pt", "portuguese": "pt"}


def _cap_traduction(texte: str):
    """« traduis <texte> en anglais » -> traduction MOT-À-MOT ASSISTÉE (concept_du_mot + dictionnaire curé).
    FAUX=0 : un mot inconnu est gardé tel quel et signalé, jamais inventé ; sortie étiquetée « mot-à-mot »."""
    m = _RE_TRADUIRE.search(texte.strip())
    if not m:
        return None
    a_traduire = m.group(1).strip().strip(" :«»\"'")
    cible = _CIBLE_TRAD.get(m.group(2).lower())
    if not a_traduire or not cible:
        return None
    try:
        import traduction
    except Exception:
        return None
    if cible not in ("en", "fr"):        # concept_du_mot couvre plus de langues mais on garantit FR<->EN curé
        tr, inconnus = traduction.traduit(a_traduire, cible)
    else:
        tr, inconnus = traduction.traduit(a_traduire, cible)
    if not tr:
        return None
    # RIEN n'a été traduit (tout est resté tel quel) -> refus honnête : « merci » était rendu comme sa
    # « traduction » allemande (vécu 2026-07-08), le texte inchangé étiqueté traduction est un mensonge doux.
    if inconnus and _normalise(tr) == _normalise(a_traduire):
        return ("Je n'ai pas ces mots dans mon dictionnaire vérifié pour cette langue — je préfère ne rien "
                "traduire plutôt que te rendre le texte inchangé comme si c'était traduit.")
    note = "  (traduction mot-à-mot assistée — à affiner)"
    if inconnus:
        note += "\nMots non trouvés (laissés tels quels, non devinés) : " + ", ".join(inconnus)
    return "%s%s" % (tr, note)


def _cap_invention_composite(texte: str):
    """OBJECTIF FINAL : « quelles inventions/relations manquent pour les X » -> attributs COMPOSITES dérivables
    (relations nouvelles « pont ∘ cible » avec témoin re-vérifié) via ia.inventions_composites (substrat_reel).
    Lourd (parcourt le graphe de faits). FAUX=0 : chaque composite est un fait re-vérifié, jamais inventé."""
    if not _RE_INVENTION_COMPO.search(texte):
        return None
    n = _normalise(texte)
    typ = next((v for mot, v in _TYPES_COMPO.items() if re.search(r"\b" + re.escape(_normalise(mot)) + r"\b", n)), None)
    if not typ:
        return None
    _ia, _ = _charge_ia()
    if not _ia or not hasattr(_ia, "inventions_composites"):
        return None
    try:
        cands = _ia.inventions_composites(typ, budget=200, k=6) or []
    except Exception:
        return None
    if not cands:
        return ("Pour les « %s », je n'ai pas trouvé de relation composée manquante avec les données chargées "
                "(sur la base complète, l'exploration serait plus riche). Rien d'inventé." % typ)
    lignes = ["Relations DÉRIVABLES qui manquent pour les « %s » (composer des relations existantes, chaque "
              "valeur re-vérifiée) :" % typ]
    for c in cands[:6]:
        s = str(c).split("\n")[0].replace("[INVENTION] attribut composite : ", "· ")
        lignes.append(s)
    lignes.append("(Ce sont des attributs composés VRAIS et systématiques — reste à juger leur utilité.)")
    return "\n".join(lignes)


def _cap_confiance(texte: str):
    """« oublie ce site X » / « bannis X » -> bannit un domaine des recherches. Léger, souverain."""
    m = re.search(r"\b(?:oublie|ignore|bannis|blackliste|ne (?:plus )?(?:utilise|consulte))\b.*?"
                  r"\b(?:le site|la source|le domaine|ce site)?\s*([a-z0-9][a-z0-9.\-]*\.[a-z]{2,})", texte, re.I)
    if not m:
        m = re.search(r"\boublie (?:ce site|cette source)\b\s*[:\-]?\s*([a-z0-9][a-z0-9.\-]*\.[a-z]{2,})?", texte, re.I)
    if m and m.lastindex and m.group(1):
        try:
            import confiance
            dom = m.group(1)
            nouveau = confiance.bannis_source(dom)
            return ("C'est noté : je ne consulterai plus « %s » dans mes recherches." % dom if nouveau
                    else "« %s » est déjà dans les sources que j'ignore." % dom)
        except Exception:
            return None
    return None


def _reponse_corrigee(texte: str):
    """Réponse d'une correction SOURCÉE de l'utilisateur pour CETTE question. Attribuée à SA source (jamais
    présentée comme la vérité vérifiée de Provara). None si aucune correction sourcée."""
    try:
        import confiance
        e = confiance.reponse_autorisee(texte)
    except Exception:
        e = None
    if e:
        return "%s  — d'après la source que tu m'avais indiquée (%s)." % (e["valeur"], e["source"])
    return None


def _cap_explication(texte: str):
    """« explique le paradoxe de X » -> explication pédagogique auto-contenue (briques Palier 2). Léger->lourd."""
    try:
        import explications
        return explications.explique(texte)
    except Exception:
        return None


def _cap_stats(texte: str):
    """Routeur STATISTIQUE NL : câble la bibliothèque Palier 2 (ia.incertitude/tendance/compare/pente/…).
    Léger côté détection, lourd si ia est requis. FAUX=0 : ne répond QUE sur intention stat reconnue, et relaie
    l'abstention honnête des fonctions (échantillon trop petit) telle quelle."""
    try:
        import fonction_stats_nl
        return fonction_stats_nl.repond_stats(texte)
    except Exception:
        return None


def _cap_audit_code(texte: str):
    """« analyse la sécurité de ce code : <bloc> » ou un bloc ``` ``` -> audit CWE (ia.audite_code). Lourd.
    FAUX=0 : constats RÉELS ou « rien détecté (pas une preuve de sécurité) » ; jamais « c'est sûr »."""
    bloc = None
    mf = re.search(r"```[a-zA-Z]*\n?(.+?)```", texte, re.S)
    if mf:
        bloc = mf.group(1)
    elif re.search(r"\b(faille|s[ée]curit[ée]|vuln[ée]rab|audit\w*)\b", texte, re.I) and re.search(
            r"\bcode\b", texte, re.I):
        m = re.search(r":\s*(.+)$", texte, re.S)
        if m and "\n" in m.group(1):
            bloc = m.group(1)
    if not bloc or len(bloc.strip()) < 10:
        return None
    langage = next((nom for nom, rx in _LANG_INDICES if rx.search(bloc)), None)
    if not langage:
        return None
    _ia, _ = _charge_ia()
    if not _ia:
        return None
    try:
        rep = _ia.audite_code(bloc, langage)
    except Exception:
        return None
    statut = getattr(rep, "statut", None)
    constats = getattr(rep, "valeur", None) or []
    if statut == "abstention" or not constats:
        return ("Je n'ai détecté aucun problème de sécurité connu dans ce code %s — attention, ce n'est PAS "
                "une preuve de sûreté (je ne vérifie que des motifs de vulnérabilité connus)." % langage)
    lignes = ["Audit de sécurité (%s) — %d constat(s) :" % (langage, len(constats))]
    for c in constats[:8]:
        titre = getattr(c, "titre", "?"); cwe = getattr(c, "cwe", ""); ligne = getattr(c, "ligne", "?")
        grav = getattr(c, "gravite", ""); rem = getattr(c, "remediation", "")
        lignes.append("· [%s, ligne %s, %s] %s%s" % (cwe, ligne, grav, titre,
                                                     (" → " + rem) if rem else ""))
    lignes.append("(Constats de motifs connus, jamais une garantie de sûreté.)")
    return "\n".join(lignes)


_GUERISON_CACHE = None            # (vocab_norm, phon_index, mots_valides) — construit une fois


def _charge_mots_valides() -> set:
    """Ensemble de mots FR valides (lexique embarqué ~19k : mot/classe/genre) pour la GARDE anti-correction :
    on ne « corrige » jamais un mot qui EST déjà un vrai mot (« pomme », « ville », « vase » restent intacts)."""
    mots: set = set()
    try:
        import lexique_fr as _LF
        base = os.path.dirname(os.path.abspath(_LF.__file__))
    except Exception:
        base = os.path.join(_HARNAIS, "src")
    for cand in (os.path.join(base, "lexique_fr_pos.jsonl"), os.path.join(_HARNAIS, "src", "lexique_fr_pos.jsonl")):
        try:
            with open(cand, encoding="utf-8") as fh:
                for ligne in fh:
                    ligne = ligne.strip()
                    if not ligne:
                        continue
                    try:
                        o = json.loads(ligne)
                    except ValueError:
                        continue
                    m = o.get("mot")
                    if m:
                        mots.add(_normalise(m))
            if mots:
                break
        except OSError:
            continue
    return mots


def _charge_verbes() -> set:
    """Infinitifs FR (~6,5k, `verbes_fr.txt`) — pour reconnaître les formes CONJUGUÉES comme des mots valides
    (le lexique 19k ne porte que des lemmes -> « divise »/« calcule » sinon non protégés et corrompus à tort)."""
    verbes: set = set()
    try:
        import lexique_fr as _LF
        base = os.path.dirname(os.path.abspath(_LF.__file__))
    except Exception:
        base = os.path.join(_HARNAIS, "src")
    for cand in (os.path.join(base, "verbes_fr.txt"), os.path.join(_HARNAIS, "src", "verbes_fr.txt")):
        try:
            with open(cand, encoding="utf-8") as fh:
                for ligne in fh:
                    v = _normalise(ligne.strip())
                    if v:
                        verbes.add(v)
            if verbes:
                break
        except OSError:
            continue
    return verbes


def _fait_forme_verbale(mn: str, verbes: set) -> bool:
    """`mn` (normalisé) est-il une forme conjuguée d'un infinitif connu ? Heuristique de reconstruction du lemme
    (1er groupe surtout : « divise/divises/divisent/divisé/divisons/divisez » -> « diviser »)."""
    if not verbes or len(mn) < 4:
        return False
    # « +re » seulement après -d/-t (rend->rendre, perd->perdre) : « ecri »+re=« écrire » protégeait à tort
    # la FAUTE « ecri » — un fragment tronqué n'est pas une forme verbale.
    cands = {mn, mn + "r", mn + "er", mn + "ir"}
    if mn.endswith(("d", "t")):
        cands.add(mn + "re")
    for suf, rempl in (("e", "er"), ("es", "er"), ("ent", "er"), ("ons", "er"), ("ez", "er"),
                       ("e", "ir"), ("ee", "er"), ("ees", "er"), ("es", "ir"),
                       # participes du 3e groupe (reconstruction du lemme ; SÛR : un candidat ne protège que
                       # s'il EST un infinitif connu) : peint->peindre, écrit->écrire, ouvert->ouvrir,
                       # mis->mettre, pris->prendre, reçu->recevoir, bu->boire, venu->venir, vu->voir…
                       ("t", "dre"), ("it", "ire"), ("ert", "rir"), ("is", "ettre"), ("is", "endre"),
                       ("u", "evoir"), ("u", "oire"), ("u", "oir"), ("enu", "enir"), ("u", "re")):
        if mn.endswith(suf):
            cands.add(mn[: len(mn) - len(suf)] + rempl)
    return any(c in verbes for c in cands)


def _guerison():
    """Prépare (une fois) l'index de correction : vocabulaire FERMÉ (social + interrogatifs + têtes de relations)
    et l'ensemble des mots FR valides. Renvoie (vocab_norm, phon_index, mots_valides) ou (None, None, None)."""
    global _GUERISON_CACHE
    if _GUERISON_CACHE is None:
        try:
            import correction_ortho as _CO
        except Exception:
            _GUERISON_CACHE = (None, None, None)
            return _GUERISON_CACHE
        vocab: set = set()
        vocab |= _SALUT | _MERCI | set(_INDICES_DEMANDE)
        for loc in (_LOC_CAVA + _LOC_ADIEU + _NOM_PHRASES + _IDENT_PHRASES):
            vocab |= {w for w in loc.split() if len(w) >= 3}
        try:                                            # têtes de relations réelles (capitale, monnaie, langue…)
            vocab |= {h for h in _attr_heads() if len(h) >= 4}
        except Exception:
            pass
        vocab |= set("bonjour salut bonsoir coucou merci comment pourquoi combien quand quel quelle quels quelles "
                     "capitale monnaie population langue president habitant continent drapeau".split())
        # participes des patrons créateur : « ecri » -> « ecrit » (le lexique des noms ne les couvre pas tous)
        vocab |= set("ecrit compose peint realise tourne invente decouvert redige pondu construit".split())
        vn, pi = _CO.construit_index(vocab)
        _GUERISON_CACHE = (vn, pi, (_charge_mots_valides(), _charge_verbes()))
    return _GUERISON_CACHE


# formes verbales IRRÉGULIÈRES fréquentes (être/avoir + auxiliaires) à PROTÉGER de la guérison : « était » n'est
# ni un nom ni reconstructible par conjugaison régulière -> sans ça, il était « corrigé » en « état » et cassait
# « qui était X ? ». Ensemble fermé, sûr (ce sont de vrais mots FR courants).
_FORMES_VERBALES_PROTEGEES = frozenset(
    "etait etais etaient etant ete est es sont suis sommes etes fut furent sera seront serait etre "
    "avait avais avaient ayant eu ont avons avez ai as sera aura auront aurait avoir "
    "faisait faisais faisaient fait faisant fera feront ferait faire "
    "pouvait pouvais peut peux peuvent pouvait pourra pourrait pouvoir "
    "devait doit dois doivent devra devrait devoir voulait veut veux veulent voudrait vouloir "
    "allait va vais vont allait ira irait aller vint vient viennent venait venir "
    # verbes en -TENIR/-IENT courants « corrigés » à tort vers un nom proche (« contient » -> « continent »,
    # vécu 2026-07-08 : « le mot chien CONTIENT combien de consonnes » cassé) : famille fermée, sûre.
    "contient contiennent contenait contenir tient tiennent tenait tenir obtient obtiennent obtenir "
    "possede possedent possedait posseder comporte comportent comportait comporter".split())
# MOTS-OUTILS FR courants à PROTÉGER de la guérison : articles/déterminants/pronoms/prépositions/conjonctions/
# adverbes fréquents. Sans ça, des mots ULTRA-courants étaient « corrigés » vers un mot-vocab proche (« des »->
# « dis », « pas »->« pays », « peu »->« peux », « tes »->« tres », « ses »->« sens »). Ensemble fermé, sûr.
_MOTS_OUTILS_PROTEGES = frozenset(
    "le la les un une des du de au aux d l ce cet cette ces mon ton son ma ta sa mes tes ses notre votre leur "
    "leurs nos vos je tu il elle on nous vous ils elles me te se lui y en moi toi soi eux "
    "et ou ni or car mais donc que qui quoi dont ou si comme quand puisque lorsque parce "
    "ne pas plus moins tres trop peu bien mal tout tous toute toutes rien tres aussi encore deja "
    "avec sans sous sur dans par pour vers chez entre apres avant depuis pendant contre selon malgre "
    "a la le du des ici la bas oui non peut etre "
    # adjectifs/interjections ULTRA-courants corrompus en contexte (« BON alors » -> « BONNE alors », bug réel
    # trouvé la nuit du 6/07 : la phrase guérie ne se dévoilait plus -> court-circuit avant (0dev))
    "bon bonne bons bonnes alors bref enfin voila voilà grand grande petit petite beau belle vieux vieille".split())
# NUMÉRAUX : ni noms ni verbes au lexique -> la guérison « corrigeait » « huit » -> « hui » (bug réel). Fermé, sûr.
_NUMERAUX_PROTEGES = frozenset(
    "zero un une deux trois quatre cinq six sept huit neuf dix onze douze treize quatorze quinze seize "
    "vingt trente quarante cinquante soixante cent cents mille million millions milliard milliards "
    "premier premiere deuxieme troisieme quatrieme cinquieme dixieme centieme "
    # abréviations mathématiques courantes « corrigées » à tort (« coef »->« chef ») : fermé, sûr.
    "coef coefs coeff coeffs".split())
_PROTEGES = _FORMES_VERBALES_PROTEGEES | _MOTS_OUTILS_PROTEGES | _NUMERAUX_PROTEGES


def _guerit_entree(texte: str) -> str:
    """Corrige les fautes de frappe de l'entrée vers un vocabulaire FERMÉ (social/interrogatif/têtes de relations),
    par FUSION distance d'édition (Damerau) ⊕ clé phonétique française, SANS jamais toucher un mot FR valide ni une
    entité. « commen vas-tu » -> « comment vas-tu ». FAUX=0 : ne rend lisible que l'INTENTION, ne change aucun fait."""
    vn, pi, valides = _guerison()
    if not vn:
        return texte
    try:
        import correction_ortho as _CO
    except Exception:
        return texte
    noms, verbes = valides if valides else (set(), set())
    # PLURIELS reconnus : « habitants » est un mot FR valide même si le lexique ne liste que « habitant » —
    # sans ça, la guérison « corrigeait » un pluriel légitime vers le singulier du vocabulaire (bug réel).
    # FILET LARGE : le lexique de noms (~19 200) est incomplet — un mot ABSENT (« plat ») était « corrigé » vers
    # un voisin valide (« plan »), corrompant le SENS. On protège AUSSI tout mot ayant une DÉFINITION dans
    # definition_nom (292k noms) : s'il est défini, c'est un vrai mot -> jamais corrigé. (est_un.definition =
    # lookup d'offset rapide ; mémoïsé par mot pour ne pas relire le disque à chaque token.)
    # ⚠ pluriels COURTS : _singulier_fr laisse les mots ≤4 lettres intacts (protège « pas »/« os ») -> « mots »
    # n'était pas reconnu comme pluriel de « mot » et se faisait « guérir » en « mode » (vécu 2026-07-08).
    # Un mot de ≥4 lettres en -s/-x dont le RADICAL est un nom du lexique est un vrai pluriel -> jamais corrigé.
    gate = (lambda mn: mn in _PROTEGES or mn in noms or _singulier_fr(mn) in noms
            or (len(mn) >= 4 and mn[-1] in "sx" and mn[:-1] in noms)
            or _fait_forme_verbale(mn, verbes) or _mot_defini(mn)) if (noms or verbes) else None
    return _CO.guerit(texte, vn, pi, gate)


_DEFINI_MEMO: dict = {}


def _mot_defini(mn: str) -> bool:
    """`mn` (normalisé) a-t-il une DÉFINITION dans definition_nom (est_un) ? Filet large anti-sur-correction de la
    guérison (un mot défini est un vrai mot). Mémoïsé ; None/erreur -> False (dégradation sûre)."""
    if len(mn) < 3:
        return False
    v = _DEFINI_MEMO.get(mn)
    if v is None:
        try:
            import est_un as _E
            v = _E.definition(mn) is not None or _singulier_fr(mn) != mn and _E.definition(_singulier_fr(mn)) is not None
        except Exception:
            v = False
        _DEFINI_MEMO[mn] = bool(v)
    return v


_PROFONDEUR: dict = {}            # conv_id -> nombre de tours (mesure de la profondeur de conversation)
# INVITES/remplissage à retirer dès qu'on n'est plus au tout premier tour : un pair ne répète pas « pose-moi une
# question » à chaque réponse. La concision N'EST PAS la brièveté (on ne coupe jamais un contenu utile) — c'est le
# ZÉRO DÉCHET : on enlève le méta conversationnel superflu, on garde tout le fond.
_INVITES = (
    " Pose-moi une question et je te réponds avec ce que je sais.",
    " Pose-moi une question et je réponds avec ce que je sais.",
    "Pose-moi une question et je te réponds avec ce que je sais.",
    "Pose-moi une question et je réponds avec ce que je sais.",
)
_DEMANDE_PROFONDEUR = re.compile(
    r"\b(explique|expliques|detaille|detailles|developpe|approfondi\w*|en\s+detail|dis[- ]?m['’]?en\s+(?:plus|davantage)|"
    r"elabore|parle[- ]?m['’]?en\s+(?:plus|davantage))\b", re.I)


def _veut_profondeur(texte: str) -> bool:
    """Le CONTEXTE réclame-t-il une réponse DÉVELOPPÉE (« explique-moi… », « détaille… », « dis-m'en plus ») ?
    Utilisé pour router une demande de détail sur une ENTITÉ vers la réponse développée (portrait/fiche)."""
    return bool(_DEMANDE_PROFONDEUR.search(_normalise(texte)))


def _ajuste_registre(reponse: str, conv_id: str, profondeur: int) -> str:
    """Adapte le REGISTRE de la réponse au contexte : retire le remplissage conversationnel (invites répétées) dès
    qu'on a dépassé le 1er tour. FAUX=0 / anti-perte : ne touche JAMAIS au contenu factuel, seulement au méta superflu."""
    if not reponse:
        return reponse
    if profondeur >= 1:
        invites = list(_INVITES)
        for v in _variantes("invite", ""):          # retire aussi les VARIANTES de formulation de l'invite
            invites.append(" " + v)
            invites.append(v)
        for inv in invites:
            reponse = reponse.replace(inv, "")
        reponse = reponse.strip()
    return reponse


def _pose_did_you_mean(t: str, conv_id):
    """Question de clarification « vouliez-vous dire … ? » sur le mot douteux de `t`, avec état EN ATTENTE
    (le « oui » du tour suivant rejoue la question corrigée via assistant_nl), ou None si aucun mot suspect.
    Message GÉNÉRIQUE (le did-you-mean est tous-domaines)."""
    sugg = _suggere_type(t)
    if not sugg:
        return None
    rep_clarif = (f"{_MSG_DYM_PREFIXE}{sugg[0]} » — vouliez-vous dire « {sugg[1]} » ? "
                  f"Réponds « oui » et je réponds directement, ou reformule.")
    try:   # état de clarification EN ATTENTE (le « oui » du tour suivant rejoue la question corrigée)
        import assistant_nl
        assistant_nl.note_clarification(conv_id, t, sugg[0], sugg[1], rep_clarif)
    except Exception:
        rep_clarif = (f"{_MSG_DYM_PREFIXE}{sugg[0]} » — vouliez-vous dire « {sugg[1]} » ? "
                      f"Reformule et je réponds.")
    return rep_clarif


# FAMILLES DE CAPS PAR ACTE — le PRIOR d'allocation vit désormais dans `sequenceur.PRIOR` (Phase 4 : la
# politique est apprise du journal de routage réel, prior en cold-start). Alias conservé pour la compat.
try:
    import sequenceur as _SEQ
    _FAMILLES_ACTES = _SEQ.PRIOR
except Exception:
    _SEQ = None
    _FAMILLES_ACTES = {}
_ROUTAGE_TICK = 0                  # décisions de routage depuis le dernier rechargement de politique
_RECHARGE_TOUS = 40               # cadence de rechargement de la politique apprise (§11 arrière-plan)


def repond(memoire, conv_id: str, texte: str, pleine: bool = False) -> str:
    """Enveloppe : calcule la réponse du noyau puis ADAPTE son registre au contexte (concision = zéro déchet ;
    profondeur allouée selon le besoin). Suit la profondeur de conversation par `conv_id`."""
    reponse = _repond_noyau(memoire, conv_id, texte, pleine=pleine)
    profondeur = _PROFONDEUR.get(conv_id, 0)
    reponse = _ajuste_registre(reponse, conv_id, profondeur)
    _PROFONDEUR[conv_id] = profondeur + 1
    return reponse


def _repond_noyau(memoire, conv_id: str, texte: str, pleine: bool = False) -> str:
    """Réponse SOUND au message `texte`. `pleine`=True autorise l'étage 2 (lourd). N'INVENTE JAMAIS.

    IMPORTANT — appeler AVANT d'indexer le message courant (sinon l'assistant se citerait sa propre question).
    `conv_id` n'est pas utilisé pour restreindre le rappel : la mémoire est CROSS-CONVERSATION (tout ce que
    l'utilisateur a dit ailleurs en privé compte aussi) — c'est l'intérêt anti-éphémère."""
    t = (texte or "").strip()
    if not t:
        return ""
    #   (0pré⁻) RÉÉCRITURE FERMÉE « combien d'habitants en France ? » -> « population de France » : la forme
    #   canonique traverse tout le pipeline (réponse FORMATÉE « Population de la France : 68 720 337
    #   habitants. ») ; la forme « combien d'habitants » n'extrayait pas l'entité (queue prise après le
    #   premier « d' » -> repli, vécu 2026-07-08). ANCRÉE en tête de phrase — le gentilé (« comment
    #   s'appellent les habitants de Lyon ») ne passe PAS par ici. Sens strictement équivalent.
    _mhab = re.match(r"^\s*combien\s+d['’]\s*habitants?\s+(en|au|aux|à|a|dans)\s+(.+?)\s*\?*\s*$",
                     t, re.IGNORECASE)
    if _mhab:
        _prep = _mhab.group(1).lower()
        t = "population " + {"au": "du ", "aux": "des "}.get(_prep, "de ") + _mhab.group(2)
    else:
        # variante sujet en tête : « la France compte combien d'habitants ? » (tombait sur un compte LEXICAL
        # de termes « habitant », vécu 2026-07-08).
        _mhab2 = re.match(r"^\s*(?:la\s+|le\s+|l['’]\s*|les\s+)?(.+?)\s+compte\s+combien\s+d['’]\s*habitants?\s*\?*\s*$",
                          t, re.IGNORECASE)
        if _mhab2:
            t = "population de " + _mhab2.group(1)
    #   (0pré) CLARIFICATION EN ATTENTE : si le tour précédent était une question de clarification de l'assistant
    #   (« vouliez-vous dire … ? ») et que ce message la CONFIRME (« oui » / le mot proposé), la question d'origine
    #   est RÉÉCRITE avec la correction CONFIRMÉE puis traitée normalement. Sound : substitution explicitement
    #   confirmée par l'utilisateur, jamais silencieuse. Refus (« non ») -> invitation à reformuler.
    try:
        import assistant_nl
        q2 = assistant_nl.reprend_clarification(conv_id, t)
    except Exception:
        q2 = None
    if q2 is not None:
        if q2 == "":
            return _varie("refus", t, _MSG_REFUS)
        t = q2
    #   (0quiz) QUIZ EN ATTENTE : le tour précédent a posé une question du défi -> la réponse est JUGÉE
    #   contre le fait vérifié mémorisé. Une nouvelle vraie demande n'est jamais prise en otage (état consommé).
    _vq = _quiz_verdict(conv_id, t)
    if _vq:
        return _vq
    #   (0conf) CORRECTION UTILISATEUR (AUTORITÉ) : si l'utilisateur a déjà corrigé cette question, sa réponse
    #       fait foi (il est le juge réel) et PRIME sur tout — connaissance, web, mémoire. FAUX=0 : appliquée
    #       telle quelle et attribuée (« tu me l'avais corrigé »).
    _corr = _reponse_corrigee(t)
    if _corr:
        return _corr
    #   (0ban) COMMANDE « oublie ce site X » : bannit un domaine des recherches futures.
    _ban = _cap_confiance(t)
    if _ban:
        return _ban
    #   (0soin) GUÉRISON ORTHOGRAPHIQUE de l'entrée (fusion Damerau ⊕ phonétique FR, vocabulaire FERMÉ) : rend
    #       l'intention lisible malgré les fautes AVANT tout matching (« commen vas-tu » -> « comment vas-tu »,
    #       « kapitale de la France » -> « capitale de la France »). FAUX=0 : ne corrige que vers des mots-outils /
    #       interrogatifs / têtes de relations, jamais une entité ni un mot FR valide -> aucun fait altéré.
    #       AMBITIEUSE MAIS HONNÊTE : la lecture corrigée est TENTÉE d'abord (réponse vérifiée directe, zéro
    #       friction) ; si elle n'aboutit à RIEN (abstention/accusé), on ne corrige pas en silence — on POSE la
    #       question (« vouliez-vous dire … ? ») sur le mot d'origine, état rejouable au tour suivant.
    t_soin = _guerit_entree(t)
    if t_soin != t:
        rep_soin = _repond_noyau(memoire, conv_id, t_soin, pleine=pleine)
        if rep_soin and not est_fallback(rep_soin):
            return rep_soin
        rep_clarif = _pose_did_you_mean(t, conv_id)
        if rep_clarif:
            return rep_clarif
        return rep_soin
    #   (0) POLITESSE (salutation/merci/adieu/« ça va ») — réponse polie immédiate, AVANT tout traitement factuel.
    #       Ne se déclenche que si le message est ENTIÈREMENT de la politesse (sinon la vraie question passe).
    poli = _politesse(t)
    if poli:
        return poli
    #   (0sal) SALUTATION COMBINÉE À UNE DEMANDE : « Bonjour comment vas-tu ? qu'est-ce que la canicule ? » —
    #       on répond au social ET on traite la demande (avant, le message ENTIER échouait en « famille
    #       inconnue »). Sound : le segment social est reconnu par l'ensemble FERMÉ existant ; le reste passe
    #       par le pipeline normal, inchangé.
    social, reste = _detache_salutation(t)
    if social and reste:
        rep_reste = _repond_noyau(memoire, conv_id, reste, pleine=pleine)
        social = social.replace(" Pose-moi une question et je te réponds avec ce que je sais.", "")
        return "%s\n\n%s" % (social, rep_reste) if rep_reste else social
    #   (0bis) MÉTA sur l'assistant (« Qui es-tu ? », « Que sais-tu faire ? ») — réponse honnête fixe, AVANT le
    #          factuel. SOUND : fullmatch sur message méta PUR -> ne capte pas une question factuelle « tu »-wrappée.
    meta = _meta_assistant(t)
    if meta:
        return meta
    #   (0ter) AUTO-DIAGNOSTIC : « diagnostic » -> combien de faits/relations Provara a réellement chargés (débogage).
    diag = _diagnostic_connaissance(t)
    if diag:
        return diag
    #   (0sms) LANGAGE SMS : « c ki ki a ecri 1984 ? » -> « c'est qui qui a ecri 1984 ? », rejoué (les étages
    #       guérison/recadrage font le reste). Carte fermée, aucun mot standard touché ; repli sans perte.
    t_sms = _desms(t)
    if t_sms != t:
        rep_sms = _rejoue(memoire, conv_id, t_sms, pleine)
        if _utile(rep_sms):
            return rep_sms
    #   (0alias) ALIAS DE PERSONNES CÉLÈBRES : « Napoléon Bonaparte » -> « Napoléon Ier » (la clé RÉELLE de
    #       toutes les relations de personnes). Carte FERMÉE d'identités incontestables (même être humain) —
    #       aucune devinette ; la question réécrite est rejouée par le pipeline complet, repli sans perte.
    t_alias = _applique_alias_personne(t)
    if t_alias != t:
        rep_alias = _rejoue(memoire, conv_id, t_alias, pleine)
        if _utile(rep_alias):
            return rep_alias
    #   (0dev) DÉVOILEMENT : « dis-moi qui a écrit 1984 » -> la question NUE est rejouée d'abord (les caps
    #       s'ancrent en ^ et rataient l'enrobage). Si elle ne produit rien de MIEUX que le générique,
    #       l'original continue son chemin normal (zéro perte, aucun fait altéré : on ne retire que du social).
    t_nu = _devoile(t)
    if t_nu != t:
        rep_nu = _rejoue(memoire, conv_id, t_nu, pleine)
        if _utile(rep_nu):
            return rep_nu
    #   (0oral) RECADRAGE ORAL : topicalisation (« la Joconde, c'est de qui ? »), clivées (« c'est qui qui… »),
    #       interrogatifs postposés (« il est né où, Napoléon ? »)… réécrits vers la forme CANONIQUE et rejoués.
    #       FAUX=0 : réordonnancement des mots de l'utilisateur, aucune invention ; repli sans perte si échec.
    t_oral = _recadre_oral(t)
    if t_oral:
        rep_oral = _rejoue(memoire, conv_id, t_oral, pleine)
        if _utile(rep_oral):
            return rep_oral
    #   (0pro) ANAPHORE INTER-TOURS : « il est mort quand ? » après « où est né Napoléon Ier ? » -> le pronom
    #       nu est substitué au dernier SUJET mémorisé et la question complète est rejouée. FAUX=0 : substitution
    #       du sujet réellement discuté, réponse toujours vérifiée ; repli sans perte si échec.
    t_pro = _resout_pronom(t, _DERNIER_SUJET.get(conv_id))
    if t_pro:
        rep_pro = _rejoue(memoire, conv_id, t_pro, pleine)
        if _utile(rep_pro):
            return rep_pro
    #   (0quater) SCHÉMA VISUEL : « montre-moi ce que tu sais sur X » -> graphe SVG des relations connues de X.
    if pleine:
        _sch = _demande_schema(t)
        if _sch:
            return _sch
    #   (0quater-bis) CAPACITÉS OUTILS (audit orphelines) — intentions EXPLICITES branchées sur ia.py, en amont
    #   du factuel. Légères (grammaire/conjugaison/graphique) toujours ; distance (coordonnées) en mode plein.
    #   Chaque handler s'abstient (None) hors de son périmètre -> le pipeline normal reprend. FAUX=0 préservé.
    for _cap in (_cap_grammaire, _cap_conjugaison, _cap_graphique):
        _r = _cap(t)
        if _r:
            return _r
    if pleine:
        # _cap_quotidien reçoit conv_id (attente à trou « pour quelle ville ? » rejouable au tour suivant).
        # CAPS NOMMÉS dans l'ordre HISTORIQUE (l'ordre = le comportement, chaque position encode un vécu).
        _caps = (("avis_critere", lambda _t: _cap_avis_critere(_t, conv_id)),
                 ("quotidien", lambda _t: _cap_quotidien(_t, conv_id)),
                 ("site", _cap_site), ("avis", lambda _t: _cap_avis(_t, conv_id)),
                 ("challenge", lambda _t: _cap_challenge(_t, conv_id)),
                 ("conversion", _cap_conversion), ("point_commun_nway", _cap_point_commun_nway),
                 ("ontologie", _cap_ontologie), ("cause", _cap_cause), ("definition", _cap_definition),
                 ("hyponymes", _cap_hyponymes), ("comptage", _cap_comptage),
                 ("classement_liste", _cap_classement_liste), ("rang", _cap_rang), ("classement", _cap_classement),
                 ("filtre", _cap_filtre), ("comparaison_nway", _cap_comparaison_nway),
                 ("comparaison", _cap_comparaison), ("meme_attribut", _cap_meme_attribut), ("devise", _cap_devise),
                 ("mesure_ambigue", _cap_mesure_ambigue), ("synonyme_tete", _cap_synonyme_tete),
                 ("dimension", _cap_dimension), ("difference", _cap_difference),
                 ("agregat_liste", _cap_agregat_liste), ("agregat", _cap_agregat),
                 ("temporel_nway", _cap_temporel_nway), ("temporel", _cap_temporel),
                 ("ecart_temporel", _cap_ecart_temporel), ("date_evenement", _cap_date_evenement),
                 ("analogie", _cap_analogie), ("portrait", _cap_portrait), ("oeuvres_de", _cap_oeuvres_de),
                 ("verif_createur", _cap_verif_createur), ("createur", _cap_createur),
                 ("naissance_compare", _cap_naissance_compare), ("succession", _cap_succession),
                 ("fait_personne", _cap_fait_personne), ("portrait_personne", _cap_portrait_personne),
                 ("record_monde", _cap_record_monde), ("fleuve_ville", _cap_fleuve_ville),
                 ("localisation", _cap_localisation), ("jeux", _cap_jeux), ("logique", _cap_logique), ("syllogisme", _cap_syllogisme), ("deduction", _cap_deduction),
                 ("contraire", _cap_contraire), ("texte", _cap_texte), ("anagramme", _cap_anagramme), ("fait_bio", _cap_fait_bio), ("protons", _cap_protons),
                 ("lunes", _cap_lunes), ("orbite", _cap_orbite), ("transitif", _cap_transitif),
                 ("inverse", _cap_inverse), ("duree", _cap_duree), ("age", _cap_age), ("stats", _cap_stats),
                 ("explication", _cap_explication), ("distance", _cap_distance), ("traduction", _cap_traduction),
                 ("code_prouve", _cap_code_prouve),
                 ("creer_ouvert", _cap_creer_ouvert), ("invention_composite", _cap_invention_composite),
                 ("invention", _cap_invention), ("audit_code", _cap_audit_code))
        # SÉQUENCEUR (Phase 4, §11) : l'acte classé (haute confiance) fait remonter SA famille de caps —
        # PRIOR ∪ appris du journal réel — en tête ; l'ordre relatif historique est préservé PARTOUT (invariant
        # de sûreté : réordonner ne change jamais la RÉPONSE, cf. sequenceur). Filet complet derrière -> zéro perte.
        _ordre, _prio, _acte5 = _caps, set(), ""
        try:
            import tronc as _T5
            _m5 = _T5.acte(t).meilleur()
            if _m5 is not None:
                _acte5 = _m5.intention if _m5.confiance >= _SEQ.SEUIL_CONF else ""
            _ordre, _prio = _SEQ.ordonne(_acte5, _caps, _m5.confiance if _m5 else 0.0)
        except Exception:
            _ordre, _prio, _acte5 = _caps, set(), ""
        for _pos_cap, (_nom_cap, _cap) in enumerate(_ordre):
            _r = _cap(t)
            if _r:
                # REGISTRE DU ROUTAGE (§16) — signal de récompense du séquenceur : à CHAQUE décision tranchée on
                # journalise (acte classé, cap gagnant, était-il prioritaire ?). Un cap gagnant HORS prio est la
                # SURPRISE dont on apprend (§9) : rejoué assez souvent, il rejoint la famille (exploration = filet).
                if _acte5:
                    try:
                        import tronc as _T6
                        _T6.note_routage(_acte5, _nom_cap, _nom_cap in _prio, position=_pos_cap)
                        # RECHARGE PÉRIODIQUE (§11 split avant/arrière-plan) : le journal grossit pendant la
                        # session ; toutes les N décisions on recharge la politique pour que l'apprentissage
                        # du jour devienne effectif SANS relancer le process (la réponse SUIVANTE est meilleure).
                        global _ROUTAGE_TICK
                        _ROUTAGE_TICK += 1
                        if _ROUTAGE_TICK % _RECHARGE_TOUS == 0 and _SEQ is not None:
                            _SEQ.recharge()
                    except Exception:
                        pass
                # SUJET mémorisé sur succès d'un cap (les anaphores inter-tours en dépendent : « où est né
                # Napoléon Ier ? » [cap fait-personne] puis « il est mort quand ? »). Garde : une vraie entité
                # nominale courte, pas un nombre ni une expression.
                if conv_id:
                    _suj = _sujet_large(t).strip(" ?.!\"'«»")
                    if _suj and 2 < len(_suj) <= 60 and len(_suj.split()) <= 5 and not _suj.isdigit():
                        _DERNIER_SUJET[conv_id] = _suj
                        _DERNIER_QUESTION[conv_id] = t
                return _r
        #   (0quater-ter) CONJONCTION multi-entités : « la population de la France et de l'Allemagne ? » -> on
        #   REJOUE « population de <chaque entité> » dans le pipeline (chaque réponse vérifiée) et on combine. En
        #   AVAL des caps spécialisés (différence/comparaison priment). FAUX=0 : découpe seule, aucune invention.
        _conj = _decoupe_conjonction(t)
        if _conj:
            tete, ents = _conj
            lignes, ok = [], 0
            for e in ents:
                _sous = _repond_noyau(memoire, conv_id, "%s de %s" % (tete, e), pleine=pleine)
                fiable = _sous and not est_fallback(_sous)
                if fiable:
                    ok += 1
                lignes.append("· %s : %s" % (e[:1].upper() + e[1:], _sous if fiable else "je ne l'ai pas en base."))
            if ok >= 1:                              # au moins une réponse vérifiée -> on rend la liste combinée
                return "%s :\n%s" % (tete[:1].upper() + tete[1:], "\n".join(lignes))
    #   (0quinquies) LANGUE MULTILINGUE : un message dans une langue supportée (en/es/de/it/pt) -> on tente d'y
    #   RÉPONDRE DANS CETTE LANGUE (question factuelle traduite vers le pipeline vérifié FR). Sinon, si c'est de
    #   l'anglais non factuel, clarification bilingue ; les autres langues non reconnues passent au pipeline FR.
    try:
        import langue as _LG
        _sw = _LG.demande_de_switch(t)                   # « réponds en espagnol » -> mémorise la préférence
    except Exception:
        _LG, _sw = None, None
    if _sw:
        _PREF_LANGUE[conv_id] = _sw
        return {"fr": "Entendu, je te réponds en français.", "en": "Alright, I'll answer in English.",
                "es": "De acuerdo, te respondo en español.", "de": "In Ordnung, ich antworte auf Deutsch.",
                "it": "Va bene, rispondo in italiano.", "pt": "Combinado, respondo em português."}.get(_sw, "Ok.")
    _lg = _LG.detecte(t) if _LG else "fr"
    _pref = _PREF_LANGUE.get(conv_id) or _PREF_LANGUE_GLOBAL[0]
    # langue CIBLE : la langue de la question si elle est écrite dans une langue non-FR supportée ; sinon la
    # préférence (sélecteur d'interface / « réponds en X ») ; sinon FR natif.
    _cible = (_lg if (_lg != "fr" and _LG and _lg in _LG.LANGUES_SUPPORTEES)
              else (_pref if _pref and _pref != "fr" else None))
    if _LG and _cible:
        _rep_lg = _cap_langue(t, lang=_cible)
        if _rep_lg:
            return _rep_lg
    if _semble_anglais(t):
        return _MSG_ANGLAIS
    #   (0ter) ALIAS DÉFINITION : « que veut dire X » / « que signifie X » / « sens du mot X » -> « définition de X »
    #          (la voie « définition de X » fonctionne déjà). Sound : réutilise une voie existante, aucun fait nouveau.
    t = _alias_definition(t)
    veut = _veut_reponse(t)
    #   PHRASE NOMINALE nue (ni question marquée, ni affirmation : « histoire du château de Chambord ») =
    #   SUJET DE RECHERCHE -> on la traite en DEMANDE (rappel mémoire, did-you-mean, clarification, « je n'ai
    #   pas l'info » honnête) plutôt qu'en fait à noter (« C'est noté » répondait à côté).
    if not veut and not _semble_affirmation(t):
        veut = True

    #   (1) CONNAISSANCE VÉRIFIÉE — tentée dès qu'on est en mode plein, MÊME sans « ? » ni mot interrogatif
    #       (« monnaie de l'arabie saoudite » tout court doit répondre). Sound : un fait vérifié sort, sinon HORS
    #       et on continue. C'est ce qui rend l'oubli du « ? » sans conséquence pour les faits du monde.
    #   GARDE NÉGATION : une question négative (« quelle n'est PAS la capitale… ») ne peut PAS être satisfaite par un
    #   lookup positif (qui répondrait le fait VRAI = FAUX ici). On saute tous les étages factuels -> mémoire/HORS.
    #   RELATIONS IMBRIQUÉES « X de [la] Y de Z » -> RAISONNEMENT COMPOSITIONNEL (P1) : on résout l'INNER (Y de Z)
    #   en une entité VÉRIFIÉE E, puis l'OUTER (X de E). FAUX=0 : chaque maillon est un lookup vérifié, abstention
    #   si un maillon manque. (Avant, on refusait tout — « monnaie de la capitale de la France » restait sans
    #   réponse ; désormais « population de la capitale de la France » = population de Paris, composée.)
    #   EXCEPTION SÛRE à la garde négation (2026-07-08) : la VÉRIFICATION d'une négation (« la capitale de la
    #   France n'est pas Lyon, si ? ») est traitée par _oui_non — qui ne confirme que du VÉRIFIÉ (« Si — X est
    #   bien Y ») ou sert le fait vérifié EXPLICITEMENT CADRÉ (« Ce que j'ai de vérifié : … »), jamais un lookup
    #   positif nu servi comme réponse à la négation.
    if pleine and _negation_bloquante(t):
        rep = _oui_non(t)
        if rep:
            return rep
    if pleine and not _negation_bloquante(t) and _est_relation_imbriquee(t) and not _est_causale(t):
        _comp = _compose_relations_n(t) or _compose_relations(t)     # N-sauts d'abord ; 2-sauts en repli
        if _comp:
            return _comp
    #   Les composées « et » ne sont PAS imbriquées (attrs séparés par « et », pas « de ») -> elles passent par _multi.
    if pleine and not _negation_bloquante(t) and not _est_relation_imbriquee(t) and not _est_causale(t):
        #   (1·svo) ORDRE LIBRE COHÉRENT — tenté AVANT le multi-questions : « la capitale, c'est quoi, pour le
        #        Japon ? » se découpe en 3 segments par virgule et partirait à tort en multi-demande. Si SVO
        #        libre y voit UNE seule question (tête + entité vérifiée), c'est elle qu'on sert. FAUX=0 (vérifié).
        #        GARDE : pas de coordination « et/puis » (une VRAIE multi-demande doit aller au multi-questions).
        _svo = None if re.search(r"\s+(?:et|puis|ainsi que)\s+", t, re.I) else _parse_svo_libre(t, conv_id)
        if _svo:
            rep, _tete, _ent = _svo
            if conv_id:
                _DERNIER_SUJET[conv_id] = _ent
                _DERNIER_QUESTION[conv_id] = "%s de %s" % (_tete, _ent)
            return rep
        #   (1·multi) DEMANDE COMPOSÉE multi-domaines (« capitale de la France ET numéro du fer ») — tentée en premier
        #        car un « et » coordonnant doit donner LES DEUX réponses, pas une seule. SOUND : ≥2 faits vérifiés requis.
        rep = _multi_questions(t, conv_id)
        if rep:
            return rep
        #   (1a) RAISONNEMENT (superlatif via relation explicite) — AVANT le lookup, pour donner la VRAIE réponse
        #        (« la plus haute montagne de France » -> mont Blanc) plutôt qu'un HORS. SOUND (pas d'argmax incomplet).
        rep = _raisonnement(t)
        if rep:
            return rep
        #   (1a-comp) COMPOSITION N-SAUTS — tentée aussi ICI (pas seulement quand `_est_relation_imbriquee` est
        #        vrai) : une chaîne à FEUILLE SUPERLATIVE (« la capitale du pays le plus peuplé d'Afrique ») n'est pas
        #        détectée comme imbriquée (l'interne n'est pas suivi de « de »). Le résolveur s'auto-protège (≥2
        #        maillons VÉRIFIÉS), donc l'essayer largement est sûr : une question simple -> None.
        rep = _compose_relations_n(t)
        if rep:
            return rep
        #   (1a-env) ENVELOPPE interrogative RÉELLE autour d'un GN composé (« sur quel continent se trouve la
        #        capitale du Japon ? », « où est né l'auteur de 1984 ? ») — tentée AVANT le lookup lourd, qui
        #        sinon résout le GN INTERNE et répond « Tokyo »/« George Orwell » (le MAUVAIS type — FAUX réel
        #        vu sur le .exe). Gardée par _ENV_PREFIXE_RE : la question doit poser une AUTRE question autour
        #        du GN (un simple « quelle est la capitale de X » reste au lookup direct). Auto-protégée :
        #        maillon interne VÉRIFIÉ exigé + réponse rejouée utile, sinon None et la cascade continue.
        if _ENV_PREFIXE_RE.search(t):
            _pfx_m = _ENV_RELATIF_RE.search(t) or _ENV_INTERNE_RE.search(t)
            if _pfx_m and _ENV_PREFIXE_RE.search(t[:_pfx_m.start()]):   # l'enveloppe est AVANT le GN interne
                rep = _compose_enveloppe(memoire, conv_id, t, pleine)
                if rep:
                    return rep
        #   (1a-sup) SUPERLATIF par ARGMAX BORNÉ, en question DIRECTE (« le pays le plus peuplé d'Afrique » ->
        #        Nigéria). Le résolveur compositionnel l'atteint déjà comme FEUILLE ; ici on sert la question nue.
        #        SOUND : compare des faits réels sur un ensemble énuméré, jamais une devinette.
        _arg = _superlatif_argmax(_HABILLAGE_RE.sub("", t).strip(" ?.!\"'«»"))
        if _arg:
            return _arg[0]
        #   (1a-calc) CALCUL DIRECT (« Combien font 4x10 ? » -> 40) : intention de calcul explicite -> résultat
        #        EXACT, AVANT le repli web (sinon une opération partait au métamoteur -> page produit hors-sujet).
        rep = _reponse_calcul(t)
        if rep:
            return rep
        #   (1a'') LOCALISATION « où se trouve X » / « coordonnées de X » -> coords ingérées (capitales + villes).
        #          SOUND : ia.coordonnees_lieu rend des coords VÉRIFIÉES ou None (inconnu -> HORS honnête).
        rep = _localisation(t)
        if rep:
            return rep
        #   (1a') VÉRIFICATION OUI/NON : « Paris est-elle la capitale de la France ? » -> « Oui. » (fait vérifié).
        #         Après le raisonnement (comparaison/superlatif) ; sound (jamais de confirmation d'un faux).
        rep = _oui_non(t)
        if rep:
            return rep
        #   (1·frais) FRAÎCHEUR (P3) : question VOLATILE (« président actuel », « dernier vainqueur ») -> source
        #   LIVE (Wikidata) préférée à la base STATIQUE qui peut être périmée. Web opt-in ; repli base sinon.
        if os.environ.get("IA_WEB") == "1" and _est_volatil(t) and not _negation_bloquante(t):
            rep = _recherche_structuree(t)
            if rep:
                return rep
        rep = _connaissance_verifiee(t, conv_id)
        if rep and _reponse_incoherente_mesure(t, rep):
            rep = None        # question de mesure (poids/taille…) mais réponse non numérique = mauvaise question -> HORS
        if rep:
            return rep
        #   (1b-syn) PARAPHRASE : le lookup exact a échoué -> reformuler un mot INCONNU par un synonyme validé
        #        (« bagnole »->« voiture », « toubib »->« médecin ») et re-vérifier. FAUX=0 : on ne renvoie qu'un
        #        fait VÉRIFIÉ, et on SIGNALE la reformulation (honnêteté). Ne substitue jamais un mot standard.
        rep = _reformule_synonymes(t, conv_id)
        if rep:
            return rep
        #   (1b) REQUÊTE INVERSE « les X d'un pays » (que le lookup par clé ne sait pas faire).
        rep = _liste_inverse(t)
        if rep:
            return rep
        #   (1b') LISTAGE moteur : « pays de l'Europe », « cite un continent ».
        rep = _listage(t)
        if rep:
            return rep
        #   (1d) FICHE ENTITÉ : « parle-moi de la France » -> synthèse (longueur variable). Après les lookups précis.
        rep = _fiche(t)
        if rep:
            return rep
        #   (1c'0) CONVERSION DE LA DERNIÈRE RÉPONSE : « et en celsius ? » après « 1811 K » -> 1537,85 °C
        #          (offset 273,15 exact). SOUND : ne convertit que la valeur-à-unité que NOUS venons de servir.
        _mcu = re.match(r"^\s*(?:et\s+)?en\s+(celsius|fahrenheit|kelvins?)\s*\?*\s*$", t, re.IGNORECASE)
        if _mcu and conv_id in _DERNIERE_VALEUR:
            _v, _u = _DERNIERE_VALEUR[conv_id]
            _cible = {"kelvins": "kelvin"}.get(_mcu.group(1).lower(), _mcu.group(1).lower())
            _table = {("K", "celsius"): (lambda x: x - 273.15, "°C"),
                      ("K", "fahrenheit"): (lambda x: (x - 273.15) * 9 / 5 + 32, "°F"),
                      ("K", "kelvin"): (lambda x: x, "K")}
            _conv = _table.get((_u, _cible))
            if _conv:
                _fmtv = lambda x: ("%.10g" % round(x, 4))
                return "%s %s = %s %s (conversion exacte)." % (_fmtv(_v), _u, _fmtv(_conv[0](_v)), _conv[1])
        #   (1c) MULTI-TOURS type A : « et sa monnaie ? » = MÊME entité, NOUVEL attribut (sujet du tour précédent).
        suj = _DERNIER_SUJET.get(conv_id)
        if suj and _est_continuation(t):
            q1 = _reformule(t, suj)
            #   REJOUER q1 dans le pipeline COMPLET d'abord (caps compris) : « et sa population ? » obtient la
            #   réponse FORMATÉE (« Population de l'Italie : 58 915 656 habitants. ») au lieu de la valeur brute
            #   « 58915656 » du lookup par clé — même choix que le type B (le pipeline sait mieux répondre).
            rep = _rejoue(memoire, conv_id, q1, pleine)
            if _utile(rep) and not (rep or "").startswith((_MSG_STRUCTURE_PREFIXE,
                                                           _MSG_STRUCTURE_COURT_PREFIXE, _MSG_DYM_PREFIXE)):
                return rep
            rep = _connaissance_verifiee(q1, conv_id)
            if rep:
                return f"{rep}  — à propos de « {suj} »"
            #   l'échange continue À TRAVERS l'abstention : « capitale du wakanda ? » (abstention structurée)
            #   puis « et sa population ? » -> abstention structurée sur « population de wakanda », pas le générique.
            _snm = _structure_non_ancree(q1, conv_id)
            if _snm:
                return _snm
        #   (1c') MULTI-TOURS type B : « et la France ? » = MÊME attribut, NOUVELLE entité (substituée dans la
        #         question précédente). Tenté APRÈS le type A : si le tour nommait un attribut, A a déjà répondu.
        derniere_q = _DERNIER_QUESTION.get(conv_id)
        if suj and derniere_q:
            ent = _nouvelle_entite(t)
            if ent and ent != suj:
                #   DEUX RÉÉCRITURES candidates : le sujet ENTIER d'abord (bon pour les vraies entités
                #   multi-mots : « arabie saoudite » -> « japon »), puis son DERNIER token — quand le « sujet »
                #   mémorisé embarque la relation (« fusion du fer »), la substitution entière donnait
                #   « point de OR » (relation perdue, vécu 2026-07-08) ; remplacer « fer » seul préserve
                #   « point de fusion du or », que le lookup résout.
                cibles = [suj]
                if " " in suj and suj.split()[-1] != ent:
                    cibles.append(suj.split()[-1])
                q2s = []
                for cible in cibles:
                    q2 = re.sub(r"\b" + re.escape(cible) + r"\b", ent, derniere_q, flags=re.IGNORECASE)
                    if q2 != derniere_q and q2 not in q2s:
                        q2s.append(q2)
                #   REJOUER q2 dans le pipeline COMPLET d'abord : « et celle de Waterloo ? » (après « quand
                #   a eu lieu la bataille de Marignan ? ») doit atteindre _cap_date_evenement -> 1815, pas le
                #   lookup brut qui répondrait un fait d'une autre nature (« champ de bataille de Waterloo »).
                _rep_web = None
                for q2 in q2s:
                    rep = _rejoue(memoire, conv_id, q2, pleine)
                    #   une réponse-aveu (« j'ai compris la structure… ») n'est PAS un succès de rejeu : la
                    #   variante suivante (« point de fusion du or ») peut, elle, résoudre -> on continue.
                    if not _utile(rep) or (rep or "").startswith((_MSG_STRUCTURE_PREFIXE,
                                                                  _MSG_STRUCTURE_COURT_PREFIXE, _MSG_DYM_PREFIXE)):
                        continue
                    #   web ON : la 1re variante (« point de or ») partait au MÉTAMOTEUR et son extrait Wikipédia
                    #   coiffait la 2e variante VÉRIFIÉE (« fusion de l'or » -> 1337 K) — vécu .exe 62. Une
                    #   réponse RAPPORTÉE est gardée en réserve, une réponse vérifiée la remplace.
                    if (rep or "").lstrip().startswith(("D'après ", "D’après ")):
                        _rep_web = _rep_web or rep
                        continue
                    return rep
                for q2 in q2s:
                    rep = _connaissance_verifiee(q2, conv_id)
                    if rep:
                        return f"{rep}  — à propos de « {ent} »"
                if _rep_web:
                    return _rep_web
                #   même continuité à travers l'abstention pour le type B (« et du mordor ? »).
                for q2 in q2s:
                    _snm = _structure_non_ancree(q2, conv_id)
                    if _snm:
                        return _snm

    #   (1·état) EXPRIMER_ÉTAT (tronc §13) — AVANT tout web : une expression d'état (lexique FERMÉ, 1re
    #   personne) ne part JAMAIS en recherche du texte littéral (G4 — vécu 2026-07-08 : « je suis perdu » +
    #   web ON servait un extrait hinative sur « j'ai perdu vs je suis perdu », hors-sujet). L'attunement du
    #   terminal mémo est ainsi REMONTÉ au-dessus de l'étage web ; il reste aussi au terminal (mode léger).
    if not veut:
        try:
            import tronc as _TE
            _att0 = _TE.attunement(t)
        except Exception:
            _att0 = None
        if _att0:
            return _att0
    #   (1·web) RECHERCHE STRUCTURÉE (opt-in réseau IA_WEB=1) : le lecteur n'a rien -> source fiable Wikidata,
    #           réponse VÉRIFIÉE + ATTRIBUÉE. Avant la mémoire pour qu'une demande factuelle sans « ? » y accède.
    #           GARDE SUBJECTIVITÉ : une question NON BORNÉE (« le plus beau pays du monde ») ne part JAMAIS au
    #           web — le métamoteur matcherait un homonyme (le FILM « Le Plus Beau Pays du monde ») au lieu du
    #           cadrage honnête « la réalité ne fixe pas de réponse unique » (rendu par le routeur de bornage).
    if (pleine and os.environ.get("IA_WEB") == "1" and not _negation_bloquante(t)
            and not _ressemble_calcul(t)):        # une opération arithmétique ne se cherche pas sur le web
        _borne_ok = True
        try:
            import classifieur_bornage as _CBn
            _borne_ok = _CBn.classe(t).statut_ontologique != _CBn.NON_BORNE
        except Exception:
            pass
        if _borne_ok:
            rep = _recherche_structuree(t)
            if rep:
                return rep
    #   (2) MÉMOIRE DE DIALOGUE — seulement si l'utilisateur DEMANDE quelque chose (sinon une affirmation
    #       déclencherait un rappel incongru). On ne retient que de vrais ÉNONCÉS : role 'user', pas le message
    #       courant, et AUCUN tour contenant « ? » (une question — même mal ponctuée « …saoudite? Si… » — n'est
    #       jamais une réponse). k généreux : questions répétées et échos 'ia' sont plus récents et éjecteraient
    #       l'énoncé d'origine par récence ; on élargit puis on filtre.
    if veut:
        # STOCKAGE d'un RAPPEL-TÂCHE (« rappelle-moi d'acheter du pain ») : accusé HONNÊTE, AVANT le rappel
        # mémoire (sinon la demande elle-même déclenchait un écho « D'après ce que tu m'as dit… » absurde).
        _ack = _cap_rappel(t)
        if _ack:
            return _ack
        # LISTE DE RAPPELS-TÂCHES (« qu'est-ce que je devais faire ? ») : on ressert TOUS les « rappelle-moi
        # de… » stockés — la promesse de _cap_rappel est TENUE ici. Requête index sur « rappelle » (le mot est
        # dans chaque tour stocké), filtre par le motif exact.
        if _RAPPEL_TODO_RE.search(t):
            _rh = memoire.rappelle("rappelle", conv_id=None, k=200, scope="prive")
            _taches = []
            for h in _rh:
                if h.get("role") != "user":
                    continue
                _mt = _RAPPEL_TACHE_RE.match(h["texte"].strip())
                if _mt:
                    _tx = (((_mt.group(2) or "") + (_mt.group(3) or "")).strip() if _mt.group(2)
                           else (_mt.group(4) or "").strip()).strip(" ?.!\"'«»")
                    _mo = (_mt.group(1) or "").strip()
                    if _mo:
                        _tx = "%s (%s)" % (_tx, _mo)
                    if _tx and _tx not in _taches:
                        _taches.append(_tx)
            if _taches:
                return "Tu m'as demandé de te rappeler :\n" + "\n".join("· %s" % x for x in _taches)
        # k TRÈS généreux : à token unique (« appelle »), rappelle départage par récence -> les questions répétées
        # et échos 'ia' (plus récents) éjecteraient l'énoncé d'origine d'un petit top-k. Lire beaucoup de postings
        # d'un index inversé reste bon marché. (Pour un historique vraiment massif, un index dédié aux ÉNONCÉS
        # serait le vrai correctif — noté comme amélioration future.)
        hits = memoire.rappelle(_expanse_rappel(t), conv_id=None, k=200, scope="prive")
        enonces = [h for h in hits
                   if h.get("role") == "user"
                   and h["texte"].strip() != t
                   # exclut TOUTE question (même sans « ? », même en SMS : « cest koi… » -> « c'est quoi… ») :
                   # une question stockée n'est pas une RÉPONSE à rappeler (sinon un « capitale du wakanda » ressort
                   # un « cest koi la capitale du japon » demandé plus tôt — non-sequitur).
                   # EXCEPTION : un RAPPEL-TÂCHE stocké (« rappelle-moi d'acheter du pain ») est un vrai énoncé
                   # ré-servable (« qu'est-ce que je dois acheter ? » doit le retrouver), pas une question.
                   and ((not _veut_reponse(h["texte"]) and not _veut_reponse(_desms(h["texte"])))
                        or _RAPPEL_TACHE_RE.match(h["texte"].strip()))]
        if enonces:
            # RE-CLASSEMENT par PERTINENCE : on choisit l'énoncé qui partage le PLUS de mots de contenu avec la
            # question (le mot DISTINCTIF départage) — « quel est mon PLAT préféré » doit rappeler « mon PLAT
            # préféré… », pas « mon FILM préféré… » (les deux partagent « préféré », seul « plat » tranche). À
            # score égal, la récence (ordre existant) l'emporte. Stable : tri par (−score, index d'origine).
            mots_q = _mots_contenu_rappel(t)
            if mots_q:
                enonces = sorted(enumerate(enonces),
                                 key=lambda ie: (-len(mots_q & _mots_contenu_rappel(ie[1]["texte"])), ie[0]))
                enonces = [e for _i, e in enonces]
            return f"{_MSG_RAPPEL_PREFIXE}« {enonces[0]['texte']} »"

        #   (2b0) PATRON APPRIS (avant le did-you-mean : un alias validé par l'utilisateur prime sur une simple
        #         suggestion de faute) — une reformulation antérieure a été apprise pour CETTE formulation ratée ->
        #         on la REJOUE (ré-aiguillage sound ; la réponse reste vérifiée). Anti-boucle : alias != texte.
        try:
            import apprentissage_patrons
            _al = apprentissage_patrons.alias(t)
        except Exception:
            _al = None
        #   GARDE FAUX=0 : un alias appris ne doit JAMAIS échanger une ENTITÉ ANCRÉE contre une autre (« wakanda »
        #   -> « france » substituerait un fait faux). Si un mot de la question ABSENT de l'alias est lui-même une
        #   entité ancrée (fait vérifié), l'alias a réécrit le sujet -> on le refuse (le patron sert à corriger une
        #   FORMULATION, pas à changer de quoi on parle).
        if _al and _normalise(_al) != _normalise(t) and not _alias_change_entite(t, _al):
            _r = _repond_noyau(memoire, conv_id, _al, pleine=pleine)
            if _r and not est_fallback(_r):
                return _r

        #   (2b) DID-YOU-MEAN — avant d'abandonner : un mot ressemble-t-il à un mot-type CONNU (faute de frappe) ?
        #        Message GÉNÉRIQUE (le did-you-mean est tous-domaines ; l'ancien texte géo « précise le pays et je
        #        liste » était incohérent quand la suggestion n'était pas géo, ex « qui a écrit … »).
        rep_clarif = _pose_did_you_mean(t, conv_id)
        if rep_clarif:
            return rep_clarif

    #   (2b-svo) PARSE SVO LIBRE — ultime recours de compréhension OUVERTE avant l'abstention : aucune règle n'a
    #        matché, mais la question porte une TÊTE DE RELATION connue + une ENTITÉ ancrable dans un ORDRE LIBRE
    #        (« du Japon, dis-moi la capitale », « Japon : monnaie ? »). On reconstruit « <tête> de <entité> » et
    #        on REJOUE en lookup vérifié. FAUX=0 : on ne renvoie QUE si le fait se vérifie ; sinon on continue.
    if veut and pleine:
        _svo = _parse_svo_libre(t, conv_id)
        if _svo:
            rep, _tete, _ent = _svo
            if conv_id:
                _DERNIER_SUJET[conv_id] = _ent
                _DERNIER_QUESTION[conv_id] = "%s de %s" % (_tete, _ent)
            return rep
    #   (2b-env) ENVELOPPE interrogative autour d'un GN composé — « sur quel continent se trouve la capitale du
    #        Japon ? » : l'enveloppe (« sur quel continent se trouve ») n'est pas une tête nominale, donc la
    #        composition N-sauts ne la voit pas, et AUCUN étage n'a su répondre (on est juste avant l'abstention
    #        — le .exe répondait « Tokyo », le MAUVAIS type). On résout le GN interne (« capitale du Japon » ->
    #        Tokyo, maillon VÉRIFIÉ), on SUBSTITUE et on REJOUE le pipeline complet (« sur quel continent se
    #        trouve Tokyo ? » -> la déduction existante, avec sa preuve). FAUX=0 : maillon montré + réponse
    #        rejouée elle-même vérifiée ; _rejoue borne la profondeur.
    if veut and pleine:
        rep = _compose_enveloppe(memoire, conv_id, t, pleine)
        if rep:
            return rep
    #   (2c) ASSISTANT AUTONOME (routeur de bornage) — la cascade factuelle vérifiée ET la mémoire n'ont RIEN :
    #        router par le gardien de bornage (cadrage non-borné honnête / calcul réellement évalué / recherche
    #        autonome sur les sources de confiance / QUESTION de clarification) plutôt que l'aveu générique.
    #        UNIQUEMENT en mode plein (en léger la connaissance n'a PAS été consultée : conclure « à chercher »
    #        serait faux) et pour une vraie DEMANDE. Sound : assistant_nl ne fabrique jamais un fait.
    if veut and pleine:
        try:
            import assistant_nl
            rep = assistant_nl.complement(t, conv_id)
        except Exception:
            rep = None
        if rep:
            # AVEU GÉNÉRIQUE (« je n'arrive pas à rattacher… ») : deux raffinements AVANT de le rendre tel quel.
            # (a) STRUCTURE RECONNUE NON ANCRÉE : si la question parse en (relation connue, entité), on dit
            #     exactement ce qui est compris et ce qui manque — bien plus utile que l'aveu générique.
            # (b) INTERNET COUPÉ par l'utilisateur : message ACTIONNABLE (réactive internet -> je cherche).
            # Les réponses UTILES d'assistant_nl (cadrage non-borné, clarification, calcul) restent inchangées.
            pfx_aveu = tuple(p for p in (getattr(assistant_nl, "_PFX_INDECIDABLE", None),
                                         getattr(assistant_nl, "_PFX_SATURATION", None)) if p)
            pfx_hors = getattr(assistant_nl, "_PFX_HORS_FAIT", None)
            est_aveu = bool(pfx_aveu) and rep.startswith(pfx_aveu)
            est_hors = bool(pfx_hors) and rep.startswith(pfx_hors)
            if est_aveu or est_hors:
                _snm = _structure_non_ancree(t, conv_id)
                if _snm:
                    return _snm if os.environ.get("IA_WEB") == "1" else _avec_web_hint(_snm, conv_id)
                if est_aveu and os.environ.get("IA_WEB") != "1":
                    return _MSG_WEB_COUPE
            return rep

    #   (3) RIEN trouvé — message selon l'intention (demande vs affirmation). En mode PLEIN (la connaissance a
    #       réellement été consultée), la brique « structure reconnue mais non ancrée » remplace le générique
    #       quand la question parse en (relation connue, entité) : dire CE QUI est compris est une information.
    if veut:
        _snm = _structure_non_ancree(t, conv_id) if pleine else None
        if pleine and os.environ.get("IA_WEB") != "1":
            return _avec_web_hint(_snm, conv_id) if _snm else _MSG_WEB_COUPE
        if _snm:
            return _snm
        indice = "" if pleine else " — ou relance sans IA_LEGER pour la connaissance générale (faits vérifiés)"
        return f"{_MSG_INCONNU_PREFIXE}{indice}."
    # affirmation : AVANT l'accusé mémo, l'ATTUNEMENT du tronc de compréhension (acte EXPRIMER_ÉTAT, carte §8) —
    # « je suis perdu » recevait « C'est noté » (vécu : le mémo à côté de la plaque = « il comprend rien »).
    # SOUND : lexique d'état FERMÉ à haute confiance ; l'état est SUPPOSÉ (« il se peut que »), jamais affirmé.
    try:
        import tronc as _TRONC
        _att = _TRONC.attunement(texte)
    except Exception:
        _att = None
    if _att:
        return _att
    # DEMANDE IMPÉRATIVE NON TRAITÉE (« équilibre la réaction H2+O2->H2O », « range mes fichiers ») : un ORDRE
    # qu'aucun cap n'a su exécuter n'est PAS une affirmation à mémoriser (« C'est noté » = garbage vécu). On
    # donne le repli HONNÊTE (ce que j'ai compris + ce que je sais faire) au lieu du mémo. Carte FERMÉE de verbes
    # d'ACTION en tête ; les verbes de MÉMORISATION (note, retiens, rappelle…) restent des mémos légitimes.
    if _est_demande_imperative(texte):
        try:
            return _TRONC.repli(texte)
        except Exception:
            return f"{_MSG_INCONNU_PREFIXE}."
    # accuser réception (le message vient d'être stocké : c'est VRAI, donc sound).
    return _varie("note", texte, _MSG_NOTE)
