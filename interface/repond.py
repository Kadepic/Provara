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
_DOSSIER_LECTEUR = os.path.join(_HARNAIS, "datasets", "lecteur")

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
        heads |= {"capitale", "monnaie", "langue", "numero", "masse", "population", "continent", "drapeau",
                  "hymne", "gentile", "superficie", "altitude", "diametre", "temperature"}
        _ATTR_HEADS_CACHE = {h for h in heads if len(h) >= 4 and h not in _GENERIQUES}
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
            print("  [VERAX] ⚠ moteur de connaissance INDISPONIBLE : %r" % _e, flush=True)
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
_SALUT = frozenset("bonjour salut bonsoir coucou hello hey allo".split())
_MERCI = frozenset("merci thanks".split())
_POLI_VOCAB = _SALUT | _MERCI | frozenset("beaucoup bien mille tres et toi vous le".split())
_LOC_ADIEU = ("au revoir", "a bientot", "a plus", "a tres bientot", "bonne nuit", "bonne soiree", "bonne journee")
_LOC_CAVA = ("ca va", "comment ca va", "comment vas tu", "comment allez vous", "comment tu vas", "tu vas bien",
             "comment ca va aujourd hui")


# — Réponse SOCIALE robuste : salutations / « ça va » / nom, même COMBINÉS et dans le désordre.
#   Sound : ne répond QUE si le message est PUREMENT social (aucun contenu factuel résiduel).
_NOM_PHRASES = ("comment t appelles tu", "comment t appeles tu", "comment tu t appelles", "comment tu t appeles",
                "quel est ton nom", "ton nom c est quoi", "c est quoi ton nom", "tu t appelles comment", "ton nom")
_IDENT_PHRASES = ("qui es tu", "tu es qui", "qui est tu", "presente toi", "c est quoi toi", "tu es quoi")
_FILLER_SOCIAL = frozenset("et toi vous stp svp s il te plait le la aussi alors donc bien tres beaucoup mille ok".split())


def _reponse_sociale(texte: str):
    """Message purement social (salutation/ça va/nom, combinés OK) -> réponse chaleureuse ; None sinon."""
    toks = _normalise(texte).replace("?", " ").replace("!", " ").replace(".", " ").split()
    if not toks:
        return None
    n = " " + " ".join(toks) + " "
    flags = {"salut": False, "cava": False, "nom": False, "ident": False, "merci": False, "adieu": False}
    groupes = ([(p, "adieu") for p in _LOC_ADIEU] + [(p, "nom") for p in _NOM_PHRASES]
               + [(p, "ident") for p in _IDENT_PHRASES] + [(p, "cava") for p in _LOC_CAVA])
    for phrase, cle in sorted(groupes, key=lambda x: len(x[0]), reverse=True):
        pad = " " + phrase + " "
        while pad in n:
            n = n.replace(pad, " "); flags[cle] = True
    reste = []
    for w in n.split():
        if w in _SALUT: flags["salut"] = True
        elif w in _MERCI: flags["merci"] = True
        elif w not in _FILLER_SOCIAL: reste.append(w)
    if reste or not any(flags.values()):     # contenu factuel résiduel -> pas (que) social
        return None
    if flags["adieu"] and not (flags["salut"] or flags["cava"] or flags["nom"] or flags["ident"]):
        return "À bientôt !"
    parts = []
    if flags["salut"]: parts.append("Bonjour !")
    if flags["cava"]: parts.append("Je vais très bien, merci\u202f\U0001F642.")
    if flags["nom"] or flags["ident"]: parts.append("Je m'appelle VERAX.")
    if flags["merci"] and not parts: parts.append("Avec plaisir !")
    parts.append("Pose-moi une question et je te réponds avec ce que je sais.")
    return " ".join(parts)


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
    "identite": "Je suis VERAX, un assistant conversationnel local et souverain. Je réponds à partir d'une base de "
                "faits vérifiés (sans GPU, hors-ligne), et je préfère dire que je ne sais pas plutôt que d'inventer.",
    "nom": "Je m'appelle VERAX. Je réponds à partir d'une base de faits vérifiés, et je préfère dire que je ne sais pas plutôt que d'inventer.",
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
_MSG_NOTE = "C'est noté, je m'en souviendrai. Tu pourras me le redemander."
_MSG_REFUS = "D'accord — reformule ta question et je réponds."
_MSG_RAPPEL_PREFIXE = "D'après ce que tu m'as dit : "
_MSG_DYM_PREFIXE = "Je ne suis pas sûr du mot « "


def est_fallback(s: str) -> bool:
    """Le texte est-il un message d'ABSENCE (rien trouvé / simple accusé de réception) ? Sert à l'enveloppe
    d'assistant_nl (porte unique) pour distinguer une vraie réponse d'un aveu d'ignorance."""
    return isinstance(s, str) and (s.startswith(_MSG_INCONNU_PREFIXE) or s == _MSG_NOTE)


def _diagnostic_connaissance(texte: str):
    """« diagnostic » / « combien de faits connais-tu » -> état RÉEL de la connaissance chargée (nb relations/faits +
    d'où viennent les données). Sert à vérifier que VERAX a bien accès à sa base (utile pour déboguer le .exe)."""
    n = _normalise(texte).strip()
    if not (n == "diagnostic" or ("combien" in n and ("relation" in n or "fait" in n or "chose" in n))):
        return None
    try:
        import os, lecteur
        _charge_ia()
        return ("Diagnostic : je connais %d relation(s) et %d fait(s). Données : %s"
                % (len(lecteur.LECTEUR.relations()), len(lecteur.LECTEUR),
                   os.environ.get("LECTEUR_DATASETS_DIR", "?")))
    except Exception as e:
        return "Diagnostic : impossible de lire l'\u00e9tat de la base (%s)" % e


def _recherche_structuree(question: str):
    """Le lecteur n'a rien -> SOURCE STRUCTURÉE fiable (Wikidata), réponse VÉRIFIÉE + ATTRIBUÉE (FAUX=0).
    Extraction SPARQL déterministe, jamais du texte libre. Réseau requis (opt-in IA_WEB=1). None si rien/erreur."""
    try:
        import veille_structure
    except Exception:
        return None
    try:
        res = veille_structure.interroge_nl(question)          # source FIABLE (Wikidata) -> fait vérifié
    except Exception:
        res = None
    if res:
        _, _, valeur, source = res
        return "%s  (trouvé sur %s)" % (valeur, source)
    try:
        wl = veille_structure.cherche_web_libre(question)      # web LIBRE (Wikipédia) -> rapport attribué + lien
    except Exception:
        wl = None
    if wl:
        extrait, titre, url = wl
        return ("D'après Wikip\u00e9dia (\u00ab %s \u00bb) : %s\n\n\U0001F517 En savoir plus : %s\n"
                "(Information trouv\u00e9e sur internet, \u00e0 v\u00e9rifier au besoin.)"
                % (titre, extrait[:420], url))
    return None


def _schema(entite: str):
    """Graphe SVG en étoile de ce que VERAX CONNAÎT sur `entite` (relations réelles du lecteur). Renvoie une chaîne
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


def repond(memoire, conv_id: str, texte: str, pleine: bool = False) -> str:
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
            return _MSG_REFUS
        t = q2
    #   (0) POLITESSE (salutation/merci/adieu/« ça va ») — réponse polie immédiate, AVANT tout traitement factuel.
    #       Ne se déclenche que si le message est ENTIÈREMENT de la politesse (sinon la vraie question passe).
    poli = _politesse(t)
    if poli:
        return poli
    #   (0bis) MÉTA sur l'assistant (« Qui es-tu ? », « Que sais-tu faire ? ») — réponse honnête fixe, AVANT le
    #          factuel. SOUND : fullmatch sur message méta PUR -> ne capte pas une question factuelle « tu »-wrappée.
    meta = _meta_assistant(t)
    if meta:
        return meta
    #   (0ter) AUTO-DIAGNOSTIC : « diagnostic » -> combien de faits/relations VERAX a réellement chargés (débogage).
    diag = _diagnostic_connaissance(t)
    if diag:
        return diag
    #   (0quater) SCHÉMA VISUEL : « montre-moi ce que tu sais sur X » -> graphe SVG des relations connues de X.
    if pleine:
        _sch = _demande_schema(t)
        if _sch:
            return _sch
    #   (0ter) ALIAS DÉFINITION : « que veut dire X » / « que signifie X » / « sens du mot X » -> « définition de X »
    #          (la voie « définition de X » fonctionne déjà). Sound : réutilise une voie existante, aucun fait nouveau.
    t = _alias_definition(t)
    veut = _veut_reponse(t)

    #   (1) CONNAISSANCE VÉRIFIÉE — tentée dès qu'on est en mode plein, MÊME sans « ? » ni mot interrogatif
    #       (« monnaie de l'arabie saoudite » tout court doit répondre). Sound : un fait vérifié sort, sinon HORS
    #       et on continue. C'est ce qui rend l'oubli du « ? » sans conséquence pour les faits du monde.
    #   GARDE NÉGATION : une question négative (« quelle n'est PAS la capitale… ») ne peut PAS être satisfaite par un
    #   lookup positif (qui répondrait le fait VRAI = FAUX ici). On saute tous les étages factuels -> mémoire/HORS.
    #   GARDE RELATIONS IMBRIQUÉES « X de [la] Y de Z » : on ne sait pas COMPOSER deux relations ; le lookup résoudrait
    #   l'INNER et renverrait une réponse du MAUVAIS TYPE (« monnaie de la capitale de la France » -> Paris ; « langue
    #   de la capitale de l'Allemagne » -> Berlin). Comme la négation, on saute TOUT le factuel -> mémoire/HORS honnête.
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
        rep = _connaissance_verifiee(t, conv_id)
        if rep and _reponse_incoherente_mesure(t, rep):
            rep = None        # question de mesure (poids/taille…) mais réponse non numérique = mauvaise question -> HORS
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
    if pleine and os.environ.get("IA_WEB") == "1" and not _negation_bloquante(t):
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
            return rep

    #   (3) RIEN trouvé — message selon l'intention (demande vs affirmation).
    if veut:
        indice = "" if pleine else " — ou relance sans IA_LEGER pour la connaissance générale (faits vérifiés)"
        return f"{_MSG_INCONNU_PREFIXE}{indice}."
    # affirmation : accuser réception (le message vient d'être stocké : c'est VRAI, donc sound).
    return _MSG_NOTE
