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
    et aux fautes de ponctuation : « ? » présent N'IMPORTE OÙ, OU un mot-indice de demande présent."""
    if "?" in texte:
        return True
    toks = set(_normalise(texte).split())
    return bool(toks & _INDICES_DEMANDE)


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
    catégoriel résolu à la place de l'attribut de mesure). Sound : ne rejette qu'une réponse non numérique."""
    return _est_question_mesure(question) and not any(c.isdigit() for c in reponse)


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


def _lookup_direct(rel_head: str, entite: str):
    """Lookup « rel_head de entite » INSENSIBLE AUX ACCENTS/CASSE, lu directement des .jsonl (contourne les
    incohérences de nommage entre relations : « Nigéria » vs « Nigeria »). FAUX=0 : normalisation d'accent =
    IDENTITÉ préservée (pas du flou Levenshtein) ; valeur renvoyée seulement si UNIQUE across la famille."""
    h = _normalise(rel_head)
    ne = _normalise(entite)
    vals = set()
    try:
        for rel in _relations():
            if rel == h or rel.split("_")[0] == h or rel.startswith(h + "_"):
                cell = _charge_direct(rel).get(ne)
                if cell and cell[1] is not None:
                    vals.add(cell[1])
    except Exception:
        return None
    return next(iter(vals)) if len(vals) == 1 else None


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
            v = _val_verifiee(ia, verifie, "%s de %s" % (rel, sous_val), rel_head=rel, entite=sous_val)
            if v is not None:
                return v, (sous_steps or []) + ["%s de %s = %s" % (rel, sous_val, v)]
        v = _val_verifiee(ia, verifie, "%s de %s" % (rel, reste), rel_head=rel, entite=reste)  # RESTE = entité littérale
        if v is not None:
            return v, ["%s de %s = %s" % (rel, reste, v)]
        return None, None
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

_REVERSE_CACHE: dict = {}     # relation -> { valeur_normalisée : (valeur_affichée, [entités triées]) }
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
    if relation in _REVERSE_CACHE:
        return _REVERSE_CACHE[relation]
    par_val: dict = {}
    chemin = os.path.join(_DOSSIER_LECTEUR, relation + ".jsonl")
    try:
        # GARDE RAM : sur la base COMPLÈTE (~73M faits), certaines relations font des MILLIONS de lignes —
        # matérialiser l'index inverse en dict coûterait des centaines de Mo chez l'utilisateur final (cache
        # sans éviction). Au-delà de 64 Mo on s'abstient (HORS honnête, comme avant) plutôt que saturer la RAM.
        if os.path.getsize(chemin) > 64 * 1024 * 1024:
            _REVERSE_CACHE[relation] = {}
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
    return res


_DIRECT_CACHE: dict = {}      # relation -> { entite_normalisée : (entite_affichée, valeur_brute) }


def _charge_direct(relation: str) -> dict:
    """Index DIRECT entité -> valeur d'une relation (lu une fois du .jsonl brut). Sert à l'argmax superlatif
    (lire l'attribut de chaque candidat sans passer par le moteur lourd)."""
    if relation in _DIRECT_CACHE:
        return _DIRECT_CACHE[relation]
    d: dict = {}
    chemin = os.path.join(_DOSSIER_LECTEUR, relation + ".jsonl")
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
    return d


# Adjectif superlatif -> relations d'attribut candidates (1re existante retenue). Domaine-extensible.
_ADJ_ATTR = {
    "peuple": ("population_pays",), "peuplee": ("population_pays",), "peuples": ("population_pays",),
    "peuplees": ("population_pays",),
    "grand": ("superficie_pays", "population_pays"), "grande": ("superficie_pays", "population_pays"),
    "grands": ("superficie_pays", "population_pays"), "grandes": ("superficie_pays", "population_pays"),
    "vaste": ("superficie_pays",), "vastes": ("superficie_pays",), "etendu": ("superficie_pays",),
    "etendue": ("superficie_pays",), "etendus": ("superficie_pays",),
    "petit": ("superficie_pays",), "petite": ("superficie_pays",), "petits": ("superficie_pays",),
    "petites": ("superficie_pays",),
    "riche": ("pib_pays", "pib_habitant_pays"), "riches": ("pib_pays", "pib_habitant_pays"),
}
# relations d'APPARTENANCE candidates par type d'entité (zone -> membres). 1re dont le reverse contient la zone.
_APPARTENANCE = {"pays": ("continent", "region_pays"), "ville": ("pays_ville",), "montagne": ("continent_montagne",)}


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


_NB_MOTS = {"un": 1, "une": 1, "deux": 2, "trois": 3, "quatre": 4, "cinq": 5, "six": 6, "sept": 7,
            "huit": 8, "neuf": 9, "dix": 10, "douze": 12, "quinze": 15, "vingt": 20}
_CLASST_RE = re.compile(
    r"(?:les|quels?\s+sont\s+les|donne(?:[- ]moi)?\s+les|cite(?:[- ]moi)?\s+les|top)\s+"
    r"(?:(\d+|un|une|deux|trois|quatre|cinq|six|sept|huit|neuf|dix|douze|quinze|vingt)\s+)?"
    r"(?:des\s+|meilleurs?\s+)?"
    r"(?:(?!plus\b|moins\b)(\w+)\s+)?(?:les\s+|la\s+|le\s+)?(?:plus|moins)\s+(\w+)"
    r"(?:\s+(\w+))?\s+(?:de\s+l['’]?|du\s|des\s|de\s|d['’]|d\s|en\s)\s*(.+?)\s*\??\s*$", re.I)


def _cap_classement(texte: str):
    """CLASSEMENT / TOP-N : « les 5 pays les plus peuplés d'Afrique » -> tri EXACT + valeurs. La machine ORDONNE des
    faits réels ; un LLM devine l'ordre. FAUX=0 : sur un ensemble énuméré, l'ordre est certain."""
    m = _CLASST_RE.search(texte)
    if not m:
        return None
    nb_tok, typ1, adj, typ2, zone = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5).strip()
    n = 5 if not nb_tok else (int(nb_tok) if nb_tok.isdigit() else _NB_MOTS.get(_normalise(nb_tok), 5))
    maximise = "moins" not in _normalise(texte).split()
    typ = next((t for t in (_normalise(typ1 or ""), _normalise(typ2 or "")) if t in _APPARTENANCE), None)
    adjn = _normalise(adj)
    if adjn not in _ADJ_ATTR and _normalise(typ2 or "") in _ADJ_ATTR:
        adjn = _normalise(typ2)
    if not typ or adjn not in _ADJ_ATTR:
        return None
    paires, _ = _membres_attribut(typ, _strip_article(zone), adjn)
    if not paires or len(paires) < 2:
        return None
    classe = paires if maximise else list(reversed(paires))
    n = max(1, min(n, len(classe)))
    lignes = ["%d. %s (%s)" % (i + 1, e, ("%d" % v if float(v).is_integer() else "%g" % v))
              for i, (e, v) in enumerate(classe[:n])]
    sens = "plus" if maximise else "moins"
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
    if zone:                                     # membres d'un type dans une zone (pays en Afrique…)
        for rel_app in _APPARTENANCE.get(sing, _APPARTENANCE.get(typn, ())):
            hit = _charge_reverse(rel_app).get(_normalise(zone))
            if hit and hit[1]:
                return "%d %s en %s (compté exactement dans mes données)." % (len(hit[1]), typ, zone)
        return None
    try:                                         # sans zone : nombre d'hyponymes réels (« combien de félins »)
        import est_un as _E
        hy = _E.hyponymes(sing, limite=100000)
    except Exception:
        hy = []
    if len(hy) >= 3:
        return "Je connais %d %s dans mes données." % (len(hy), typ)
    return None


def _superlatif_argmax(expr: str):
    """FEUILLE SUPERLATIVE par ARGMAX BORNÉ : « le pays le plus peuplé d'Afrique » -> Nigeria, en comparant TOUS les
    membres énumérés (les pays d'Afrique) sur un attribut vérifié (population). SOUND tant que l'ensemble est complet :
    on ne devine pas, on COMPARE des faits réels et on peut montrer le décompte. Renvoie (entité, étape) ou None."""
    nz = _normalise(expr)
    toks = nz.split()
    if "plus" not in toks and "moins" not in toks:
        return None
    maximise = "moins" not in toks
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
    attr_rel = next((r for r in _ADJ_ATTR[adj] if _charge_direct(r)), None)
    if not attr_rel:
        return None
    # membres = entités du type dont l'appartenance == zone (reverse-lookup)
    membres = None
    for rel_app in _APPARTENANCE[typ]:
        rev = _charge_reverse(rel_app)
        hit = rev.get(zone) or next((v for k, v in rev.items() if k == zone), None)
        if hit and hit[1]:
            membres = hit[1]
            break
    if not membres:
        return None
    attr = _charge_direct(attr_rel)
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
        if len(tok) < 5 or tok in cibles or _mot_reel(tok):
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
        return _ALIAS.get(w) or (_ALIAS.get(w[:-1]) if w.endswith(("s", "x")) else None) or w

    def _liste_plausible(rel) -> bool:
        rtoks = [t for t in rel.split("_") if len(t) >= 3 and t not in _GENERIQUES]
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
    candidats = [rel for rel in _relations()
                 if any(len(tk) >= 3 and tk not in _GENERIQUES and tk in demandes for tk in rel.split("_"))
                 and (intent or _liste_plausible(rel))]
    for rel in candidats:
        par_val = _charge_reverse(rel)
        if not par_val:
            continue
        rtoks = set(rel.split("_"))    # garde anti-coïncidence : la VALEUR ne doit pas être un mot du NOM de la
        #                                relation (« capitale de la LUNE » : « lune » est à la fois le token de
        #                                `plus_grande_lune` ET sa valeur -> on ne liste pas « terre »).
        best = None       # la VALEUR (la plus longue) nommée dans la question -> ancre la requête
        for vn, (disp, ents) in par_val.items():
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
    if not lieu:
        return None
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
        return f"{prefixe}{fait.valeur}"          # source vérifiée en interne, non affichée (préférence Yohan)
    # REPLI FAMILLE : « continent de France » peut ne pas matcher un gabarit direct alors que la relation existe
    # sous un nom de famille (continent_pays…). On parse « rel de entité » et on essaie la famille (unicité exigée,
    # FAUX=0). N'affecte JAMAIS une réponse déjà résolue (on n'arrive ici que si le DATA a rendu HORS).
    mfam = re.match(r"^\s*(?:quel(?:le)?s?\s+(?:est|sont)\s+)?(?:la\s+|le\s+|les\s+|l['] ?)?"
                    r"([\wà-ÿ]+)\s+(?:de\s+la|de\s+l['] ?|du|des|de)\s+(?:la\s+|le\s+|les\s+|l['] ?)?(.+?)\s*\??\s*$",
                    question, re.I)
    if mfam and _normalise(mfam.group(1)) in _attr_heads():
        vf = _val_par_famille(ia, mfam.group(1).strip(), mfam.group(2).strip(" ?.\"'«»"))
        if vf:
            return str(vf)
    # Le DATA n'a rien : tenter un SOUS-SYSTÈME FONCTION (morse/OTAN/masse molaire/complément ADN). Sound : le
    # moteur renvoie VÉRIFIÉ ou HORS (jamais inventé). On exige un mot-clé fort -> aucune question DATA mal routée.
    return _fonction_calculee(question)


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
    r"additionn\w+|soustrai\w+|divis\w+)\b|=\s*\??\s*$|\begale?\s*\??\s*$")


def _reponse_calcul(texte: str) -> str | None:
    """CALCUL DIRECT mono-question (« Combien font 4x10 ? » -> « 40 »). Tenté AVANT le repli web pour qu'une
    intention de calcul claire obtienne son résultat EXACT plutôt qu'une page web sans rapport. FAUX=0 : on ne
    renvoie que le verdict VÉRIFIÉ du moteur (entiers exacts) ; sinon None (abstention honnête, pas d'arrondi).
    Le « x » n'est converti en « × » QUE si l'intention de calcul est explicite (sinon « 4 x 100 » reste intact)."""
    if not _CALC_INTENT.search(_normalise(texte)):
        return None
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
    except Exception:
        pass
    return None


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
    return cand


def _sujet_de(texte: str) -> str:
    """Sujet (entité) d'une question = ce qui suit la dernière préposition (« capitale du JAPON » -> « japon »)."""
    m = re.search(r"\b(?:de la|de l'|de l|du|des|de|en|au|aux)\s+(.+?)[\s?]*$", texte.strip(), re.IGNORECASE)
    return m.group(1).strip() if m else ""


_VOLATIL_RE = re.compile(
    r"\b(actuel|actuelle|actuels|actuelles|actuellement|aujourd'?hui|maintenant|désormais|present|présentement|"
    r"current|latest|dernier|dernière|derniers|dernières|récent|récente|en ce moment|à ce jour|cette année|"
    r"en 20\d\d)\b", re.I)


def _est_volatil(texte: str) -> bool:
    """Question à réponse POTENTIELLEMENT PÉRIMÉE dans la base statique (« président ACTUEL », « DERNIER
    vainqueur », « en 2026 ») : on préférera la source LIVE (fraîcheur) quand le web est autorisé. FAUX=0
    inchangé (la source live est vérifiée + attribuée ; repli sur la base si indisponible)."""
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
        if not prenom and (flags["nom"] or flags["ident"]): parts.append("My name is Provara.")
        if flags["merci"] and not parts: parts.append("You're welcome!")
        parts.append("For now I answer best in FRENCH (a full English mode is on the roadmap) — "
                     "try « capitale de l'Espagne » or « population du Japon ».")
        return " ".join(parts)
    parts = []
    if prenom: parts.append(("Bonjour %s, enchantée \U0001F642." % prenom) if flags["salut"] else ("Enchantée, %s \U0001F642." % prenom))
    elif flags["salut"]: parts.append(_varie("salut", texte, "Bonjour !"))
    if flags["cava"]: parts.append(_varie("cava", texte, "Je vais très bien, merci 🙂."))
    if not prenom and (flags["nom"] or flags["ident"]): parts.append("Je m'appelle Provara.")
    if flags["merci"] and not parts: parts.append("Avec plaisir !")
    parts.append(_varie("invite", texte, "Pose-moi une question et je te réponds avec ce que je sais."))
    return " ".join(parts)


_SEG_PHRASE_RE = re.compile(r"(?<=[.!?])\s+")
_SALUT_TETE_RE = re.compile(r"^\s*(bonjour|salut|bonsoir|coucou|hello|hi|hey)[ ,!]+(.{4,})$", re.I | re.S)


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
    Sound : jamais de confirmation d'un faux (mismatch -> None -> flux normal), jamais de « Non » (multi-valué)."""
    m = _OUINON_RE.match(texte.strip())
    if not m:
        return None
    gauche, droite = m.group(1).strip(), m.group(2).strip()
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
            return _META_REPONSES[cle]
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
        or s == _MSG_NOTE or s in _variantes("note", _MSG_NOTE))


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
    if not (n == "diagnostic" or ("combien" in n and ("relation" in n or "fait" in n or "chose" in n))):
        return None
    try:
        import os, lecteur
        _charge_ia()
        return ("Diagnostic : je connais %d relation(s) et %d fait(s). Données : %s · build %s · recherche web %s"
                % (len(lecteur.LECTEUR.relations()), len(lecteur.LECTEUR),
                   os.environ.get("LECTEUR_DATASETS_DIR", "?"), _build_id(),
                   "activée" if os.environ.get("IA_WEB") == "1" else "désactivée"))
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
                 r"(?:du\s+mot\s+|de\s+l['’]|de\s+la\s+|de\s+|d['’])\s*['\"«]?\s*([\wà-ÿ][\wà-ÿ'\-]*)\s*['\"»]?\s*\??\s*$",
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
    if not re.search(r"\bconjug(?:ue|ues|uer|aison)\b", texte, re.I):
        return None
    m = re.search(r"\b([a-zàâäéèêëïîôöùûüç]+(?:er|ir|re))\b", texte, re.I)
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
    if not m:
        return None
    a, b = m.group(1).strip(" ?.\"'«»"), m.group(2).strip(" ?.\"'«»")
    _ia, _ = _charge_ia()
    if not _ia:
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


def _cap_invention(texte: str):
    """« comment [faire] X sans Y » / « que manque-t-il pour X » -> reformulation PHYSIQUE du besoin (moteur
    d'invention besoin.py, la vision produit). FAUX=0 : ne répond QUE pour un besoin du catalogue physique ;
    besoin inconnu -> None (le web/pipeline prend le relais). Léger."""
    besoin_txt = None
    m = re.search(r"\bque\s+manque[\s-]*t[\s-]*il\s+pour\s+(.+?)\s*\??\s*$", texte, re.I)
    if m:
        besoin_txt = m.group(1)
    if besoin_txt is None:
        m = re.search(r"\bcomment\s+(?:faire\s+pour\s+|je\s+peux\s+|)(.+?)\s+sans\s+.+?\s*\??\s*$", texte, re.I)
        if m:
            besoin_txt = m.group(1)
    if besoin_txt is None:
        return None
    besoin_txt = besoin_txt.strip(" ?.\"'«»")
    try:
        import besoin as _BSN
        d = _BSN.decompose(besoin_txt)
    except Exception:
        return None
    if not isinstance(d, dict) or d.get("statut") != "decompose":
        return None                                       # hors catalogue physique -> pipeline continue
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


def _cap_ontologie(texte: str):
    """RAISONNEMENT is-a conversationnel (« un chat est-il un mammifère ? » -> « Oui, … »; « qu'ont en commun le
    chat et le requin ? » -> « animal »), depuis la source SAINE `est_un` (classe_* curées + genre des définitions).
    FAUX=0 : « Oui » seulement si dérivable ; jamais de « Non » affirmé (monde ouvert) — on énonce plutôt le vrai
    genre connu. Le réseau de foule (JeuxDeMots) N'est PAS utilisé ici (trop bruité pour une assertion)."""
    try:
        import est_un as _E
    except Exception:
        return None
    m = _ONTO_ESTUN_RE.search(texte) or _ONTO_ESTUN2_RE.search(texte)
    if m:
        x, y = m.group(1).strip(), m.group(2).strip()
        if _normalise(x) == _normalise(y):
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
    r"|d[ée]finition\s+d[eu'’]\s*(?:un\s|une\s|le\s|la\s|l['’])?\s*"
    r"|d[ée]finis[- ]?(?:moi\s+)?(?:un\s|une\s|le\s|la\s|l['’])?\s*"
    r"|qu['’ ]?est[- ]ce\s+qu['’e]?\s*)"
    r"([\wà-ÿ][\wà-ÿ'’\- ]*?)\s*\??\s*$", re.I)
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


def _cap_definition(texte: str):
    """« C'est quoi X ? » / « qu'est-ce qu'un X ? » / « définition de X » -> définition VÉRIFIÉE de la base
    (definition_nom : 292k+ noms du Wiktionnaire, puis definition_* de domaine). FAUX=0 : texte réel ou None."""
    m = _DEF_RE.match(texte)
    if not m:
        return None
    ent = _strip_article(m.group(1).strip())
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


_HYPO_RES = (
    re.compile(r"\b(?:exemples?|types?|sortes?|esp[eè]ces?|vari[ée]t[ée]s?)\s+d[e'’]\s*(?:la\s|le\s|les\s|l['’])?"
               r"(.+?)\s*\??\s*$", re.I),
    re.compile(r"^\s*(?:quels?|quelles?)\s+sont\s+les\s+(.+?)\s*\??\s*$", re.I),
    re.compile(r"\b(?:cite|citez|liste|listez|nomme|nommez|donne(?:[- ]moi)?|donnez[- ]moi)\b.*?"
               r"\b(?:des|les|quelques|plusieurs)\s+(.+?)\s*\??\s*$", re.I),
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
    sing = cat[:-1] if (cat.endswith(("s", "x")) and len(cat) > 4) else cat
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
    r"(?:est[- ]ce\s+qu[e'’]?\s*)?(.+?)\s+(?:orbite|gravite|tourne)\b[^?]*?"
    r"(?:autour\s+)?(?:de\s+la\s+|de\s+l['’]|du\s+|des\s+|de\s+|d['’])?([\wà-ÿ'’\- ]+?)\s*\??\s*$", re.I)
_SYSTEME_RE = re.compile(
    r"(?:est[- ]ce\s+qu[e'’]?\s*)?(.+?)\s+(?:fait[- ](?:il|elle)\s+partie|fait\s+partie|est[- ](?:il|elle)|appartient|"
    r"est\s+dans)"
    r"[^?]*?syst[eè]me\s+(?:(solaire)|(?:de\s+(?:la\s+|l['’])?|d['’])?([\wà-ÿ'’\- ]+?))\s*\??\s*$", re.I)


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
    if not par or ns not in par:
        return None
    # marche la chaîne parentale : sujet -> parent -> parent... jusqu'à la cible (dérivation transitive)
    chaine = [par[ns][0]]
    vus, cur = {ns}, ns
    atteint = False
    for _ in range(20):
        cell = par.get(cur)
        if not cell:
            break
        parent = cell[1]
        chaine.append(parent)
        if _normalise(parent) == cible:
            atteint = True
            break
        np = _normalise(parent)
        if np in vus:
            break
        vus.add(np)
        cur = np
    if not atteint or len(chaine) < 2:
        return None
    # DÉCOUVERTE : on valide la transitivité (cohérente) et on rejette la symétrie (contre-exemple), pour l'afficher
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
    if len(chaine) == 2:                                # relation directe, pas une dérivation
        return None
    _ASTRO_ART = {"soleil": "le Soleil", "terre": "la Terre", "lune": "la Lune"}
    chaine = [_ASTRO_ART.get(_normalise(c), c) for c in chaine]
    derivation = "%s orbite %s" % (chaine[0], ", qui orbite ".join(chaine[1:]))
    return "Oui — je le déduis : %s%s." % (derivation, note)


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
    cands = {mn, mn + "r", mn + "er", mn + "ir", mn + "re"}
    for suf, rempl in (("e", "er"), ("es", "er"), ("ent", "er"), ("ons", "er"), ("ez", "er"),
                       ("e", "ir"), ("ee", "er"), ("ees", "er"), ("es", "ir")):
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
        vn, pi = _CO.construit_index(vocab)
        _GUERISON_CACHE = (vn, pi, (_charge_mots_valides(), _charge_verbes()))
    return _GUERISON_CACHE


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
    gate = (lambda mn: mn in noms or _fait_forme_verbale(mn, verbes)) if (noms or verbes) else None
    return _CO.guerit(texte, vn, pi, gate)


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
    t = _guerit_entree(t)
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
        for _cap in (_cap_ontologie, _cap_cause, _cap_definition, _cap_hyponymes, _cap_comptage, _cap_classement, _cap_portrait, _cap_deduction, _cap_orbite, _cap_stats, _cap_explication, _cap_distance, _cap_traduction, _cap_invention_composite, _cap_invention, _cap_audit_code):
            _r = _cap(t)
            if _r:
                return _r
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
    if pleine and not _negation_bloquante(t) and _est_relation_imbriquee(t) and not _est_causale(t):
        _comp = _compose_relations_n(t) or _compose_relations(t)     # N-sauts d'abord ; 2-sauts en repli
        if _comp:
            return _comp
    #   Les composées « et » ne sont PAS imbriquées (attrs séparés par « et », pas « de ») -> elles passent par _multi.
    if pleine and not _negation_bloquante(t) and not _est_relation_imbriquee(t) and not _est_causale(t):
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
        #   (1c) MULTI-TOURS type A : « et sa monnaie ? » = MÊME entité, NOUVEL attribut (sujet du tour précédent).
        suj = _DERNIER_SUJET.get(conv_id)
        if suj and _est_continuation(t):
            rep = _connaissance_verifiee(_reformule(t, suj), conv_id)
            if rep:
                return f"{rep}  — à propos de « {suj} »"
        #   (1c') MULTI-TOURS type B : « et la France ? » = MÊME attribut, NOUVELLE entité (substituée dans la
        #         question précédente). Tenté APRÈS le type A : si le tour nommait un attribut, A a déjà répondu.
        derniere_q = _DERNIER_QUESTION.get(conv_id)
        if suj and derniere_q:
            ent = _nouvelle_entite(t)
            if ent and ent != suj:
                q2 = re.sub(r"\b" + re.escape(suj) + r"\b", ent, derniere_q, flags=re.IGNORECASE)
                if q2 != derniere_q:
                    rep = _connaissance_verifiee(q2, conv_id)
                    if rep:
                        return f"{rep}  — à propos de « {ent} »"

    #   (1·web) RECHERCHE STRUCTURÉE (opt-in réseau IA_WEB=1) : le lecteur n'a rien -> source fiable Wikidata,
    #           réponse VÉRIFIÉE + ATTRIBUÉE. Avant la mémoire pour qu'une demande factuelle sans « ? » y accède.
    if (pleine and os.environ.get("IA_WEB") == "1" and not _negation_bloquante(t)
            and not _ressemble_calcul(t)):        # une opération arithmétique ne se cherche pas sur le web
        rep = _recherche_structuree(t)
        if rep:
            return rep
    #   (2) MÉMOIRE DE DIALOGUE — seulement si l'utilisateur DEMANDE quelque chose (sinon une affirmation
    #       déclencherait un rappel incongru). On ne retient que de vrais ÉNONCÉS : role 'user', pas le message
    #       courant, et AUCUN tour contenant « ? » (une question — même mal ponctuée « …saoudite? Si… » — n'est
    #       jamais une réponse). k généreux : questions répétées et échos 'ia' sont plus récents et éjecteraient
    #       l'énoncé d'origine par récence ; on élargit puis on filtre.
    if veut:
        # k TRÈS généreux : à token unique (« appelle »), rappelle départage par récence -> les questions répétées
        # et échos 'ia' (plus récents) éjecteraient l'énoncé d'origine d'un petit top-k. Lire beaucoup de postings
        # d'un index inversé reste bon marché. (Pour un historique vraiment massif, un index dédié aux ÉNONCÉS
        # serait le vrai correctif — noté comme amélioration future.)
        hits = memoire.rappelle(_expanse_rappel(t), conv_id=None, k=200, scope="prive")
        enonces = [h for h in hits
                   if h.get("role") == "user"
                   and h["texte"].strip() != t
                   and not _veut_reponse(h["texte"])]   # exclut TOUTE question (même sans « ? ») : pas une réponse
        if enonces:
            return f"{_MSG_RAPPEL_PREFIXE}« {enonces[0]['texte']} »"

        #   (2b0) PATRON APPRIS (avant le did-you-mean : un alias validé par l'utilisateur prime sur une simple
        #         suggestion de faute) — une reformulation antérieure a été apprise pour CETTE formulation ratée ->
        #         on la REJOUE (ré-aiguillage sound ; la réponse reste vérifiée). Anti-boucle : alias != texte.
        try:
            import apprentissage_patrons
            _al = apprentissage_patrons.alias(t)
        except Exception:
            _al = None
        if _al and _normalise(_al) != _normalise(t):
            _r = _repond_noyau(memoire, conv_id, _al, pleine=pleine)
            if _r and not est_fallback(_r):
                return _r

        #   (2b) DID-YOU-MEAN — avant d'abandonner : un mot ressemble-t-il à un mot-type CONNU (faute de frappe) ?
        #        Message GÉNÉRIQUE (le did-you-mean est tous-domaines ; l'ancien texte géo « précise le pays et je
        #        liste » était incohérent quand la suggestion n'était pas géo, ex « qui a écrit … »).
        sugg = _suggere_type(t)
        if sugg:
            rep_clarif = (f"{_MSG_DYM_PREFIXE}{sugg[0]} » — vouliez-vous dire « {sugg[1]} » ? "
                          f"Réponds « oui » et je réponds directement, ou reformule.")
            try:   # état de clarification EN ATTENTE (le « oui » du tour suivant rejoue la question corrigée)
                import assistant_nl
                assistant_nl.note_clarification(conv_id, t, sugg[0], sugg[1], rep_clarif)
            except Exception:
                rep_clarif = (f"{_MSG_DYM_PREFIXE}{sugg[0]} » — vouliez-vous dire « {sugg[1]} » ? "
                              f"Reformule et je réponds.")
            return rep_clarif

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
            # INTERNET COUPÉ par l'utilisateur : ses aveux d'impuissance génériques (« je n'arrive pas à
            # rattacher… ») deviennent un message ACTIONNABLE (réactive internet -> je cherche). Ses réponses
            # UTILES (cadrage non-borné, clarification, calcul) restent prioritaires et inchangées.
            if os.environ.get("IA_WEB") != "1":
                prefixes = tuple(p for p in (getattr(assistant_nl, "_PFX_INDECIDABLE", None),
                                             getattr(assistant_nl, "_PFX_SATURATION", None)) if p)
                if prefixes and rep.startswith(prefixes):
                    return _MSG_WEB_COUPE
            return rep

    #   (3) RIEN trouvé — message selon l'intention (demande vs affirmation).
    if veut:
        if pleine and os.environ.get("IA_WEB") != "1":
            return _MSG_WEB_COUPE
        indice = "" if pleine else " — ou relance sans IA_LEGER pour la connaissance générale (faits vérifiés)"
        return f"{_MSG_INCONNU_PREFIXE}{indice}."
    # affirmation : accuser réception (le message vient d'être stocké : c'est VRAI, donc sound).
    return _varie("note", texte, _MSG_NOTE)
