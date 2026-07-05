"""
ASSISTANT NL — la PORTE CONVERSATIONNELLE AUTONOME (« gros bond », mandat nuit 2026-07-03).

Yohan : « il faut que mon IA puisse COMPRENDRE ce que je dis et FAIRE les recherches associées au lieu que ce
soit toi qui t'en occupes ; si elle veut que je précise, QU'ELLE ME POSE LES QUESTIONS. »

Ce module N'AJOUTE AUCUN étage de connaissance : il RÉUTILISE le pipeline conversationnel existant
(interface/repond.py : politesse, méta, cascade factuelle vérifiée, mémoire de dialogue, did-you-mean) et le
complète de TROIS capacités nouvelles :

  1. ROUTAGE PAR BORNAGE après HORS : quand la cascade factuelle n'a rien, le gardien `classifieur_bornage`
     décide du régime — non-borné -> cadrage honnête (pas de « fait » à trancher) ; calcul réellement évalué ->
     FAIT ; borné sans juge -> RECHERCHE AUTONOME sur les sources de confiance (veille.py, opt-in IA_WEB=1) ;
     indécidable -> QUESTION DE CLARIFICATION (on demande, on ne devine jamais).
  2. CLARIFICATION AVEC ÉTAT : une question de clarification posée (« vouliez-vous dire X ? ») reste EN ATTENTE
     par conversation ; si le tour suivant la CONFIRME (« oui » / le mot proposé), la question d'origine est
     RÉÉCRITE avec la correction CONFIRMÉE puis traitée normalement. Jamais de substitution silencieuse.
  3. ENVELOPPE UNIFORME `Reponse` (statut fait/supposition/clarification/echange/hors + texte + régime + source)
     pour absorber l'hétérogénéité des retours du stack — porte unique `ia.assistant(question)`.

FAUX=0 : ce module ne FABRIQUE jamais un fait. Les seules affirmations sortantes viennent (a) du pipeline vérifié
existant, (b) d'un calcul RÉELLEMENT évalué qui COUVRE TOUTE la question (juge arithmétique AST du classifieur).
La classification de l'enveloppe est POSITIVE (chaque texte terminal non-factuel est reconnu par sa constante) —
jamais un défaut « fait » (faille fermée par la passe adverse 2026-07-03). Le rappel de dialogue est typé
SUPPOSITION RAPPORTÉE (l'utilisateur l'a dit — vrai ; le contenu n'est pas vérifié). Le web reste SUPPOSITION
RAPPORTÉE tant que non corroboré. Au doute -> clarification ou HORS honnête.

IMPORT LÉGER (OOM-safe) : top-level = stdlib + base_faits + classifieur_bornage (stdlib pur). Le pipeline complet
(interface/repond.py, qui charge `ia` paresseusement) et `veille`/`conversation` sont importés PARESSEUSEMENT.
"""
from __future__ import annotations

import dataclasses
import itertools
import os
import re
import threading
import time

from base_faits import normalise as _normalise
import classifieur_bornage as _CB

_ICI = (os.environ.get("VERAX_ROOT") or os.path.dirname(os.path.abspath(__file__)))

# ── statuts de l'enveloppe (la porte unique parle UNE langue) ──
FAIT = "fait"                    # affirmation vérifiée (lecteur/calcul couvrant) avec provenance
SUPPOSITION = "supposition"      # cadrage non-borné / rapporté — JAMAIS servi comme un fait
CLARIFICATION = "clarification"  # l'assistant POSE une question (jamais deviner)
ECHANGE = "echange"              # social/méta (politesse, « qui es-tu »)
HORS = "hors"                    # abstention honnête


@dataclasses.dataclass(frozen=True)
class Reponse:
    """Enveloppe uniforme d'une réponse d'assistant : ce qui est dit, son statut, et d'où ça vient."""
    statut: str
    texte: str
    regime: str = ""      # régime du contrat d'atome décidé par le gardien de bornage ('' si non consulté)
    source: str = ""      # provenance quand FAIT / détail technique honnête sinon ('' si rien)
    attente: str = ""     # pour CLARIFICATION : ce que le tour suivant doit préciser


# ── état par conversation (en-process, même convention que _DERNIER_SUJET de l'interface) ──
# _EN_ATTENTE[conv] = {"type": "dym", question, mot, proposition} (did-you-mean) ou {"type": "reformule"}.
_EN_ATTENTE: dict = {}
_INDECIS: dict = {}       # conv_id -> nb de clarifications « indécidable » consécutives (anti-boucle)
_VERROU = threading.Lock()
_CPT = itertools.count(1)  # ids de conversation jetables pour la porte unique sans conv_id (pas de clé partagée)

# Confirmations/refus (normalisés sans accents). Locutions FERMÉES + règle de TÊTE (« oui oui », « non merci ») —
# un message plus long (« oui mais pour la Loire ») n'est PAS une confirmation : nouvelle question, pas de
# substitution douteuse.
_LOC_OUI = frozenset(("d accord", "tout a fait", "c est ca", "bien sur", "oui c est ca", "oui exactement",
                      "oui merci", "oui stp", "oui s il te plait"))
_TETE_OUI = frozenset(("oui", "ouais", "yes", "ok", "exact", "exactement", "voila", "carrement", "volontiers"))
_LOC_NON = frozenset(("pas ca", "pas du tout", "non merci", "non pas ca"))
_TETE_NON = frozenset(("non", "nan", "no"))

# Transport veille injectable (tests OFFLINE) : None = transport réel urllib de veille.py.
_TRANSPORT = None


def _est_confirmation(tn: str) -> bool:
    toks = tn.split()
    return bool(toks) and (tn in _LOC_OUI or (toks[0] in _TETE_OUI and len(toks) <= 2))


def _est_refus(tn: str) -> bool:
    toks = tn.split()
    return bool(toks) and (tn in _LOC_NON or (toks[0] in _TETE_NON and len(toks) <= 2))


# ————————————————————————— CLARIFICATION AVEC ÉTAT (capacité 2) —————————————————————————
def note_clarification(conv_id, question: str, mot: str, proposition: str, texte: str) -> None:
    """Enregistre une clarification did-you-mean EN ATTENTE pour `conv_id`. `mot` = le mot douteux de `question`,
    `proposition` = la forme proposée, `texte` = la question posée à l'utilisateur (pour trace)."""
    if not conv_id:
        return
    _EN_ATTENTE[conv_id] = {"type": "dym", "question": question, "mot": mot, "proposition": proposition}


def note_reformulation(conv_id) -> None:
    """Enregistre qu'une DEMANDE DE REFORMULATION est en attente : un simple « oui »/« non » au tour suivant
    recevra l'invitation à reformuler au lieu d'un « C'est noté » incongru."""
    if conv_id:
        _EN_ATTENTE[conv_id] = {"type": "reformule"}


def oublie_etat(conv_id) -> None:
    """Purge l'état en-process de la conversation (pendants RGPD de `oublie`) : plus rien à rejouer."""
    _EN_ATTENTE.pop(conv_id, None)
    _INDECIS.pop(conv_id, None)


def reprend_clarification(conv_id, texte: str):
    """Résout la clarification EN ATTENTE de `conv_id` avec la réponse `texte`. État consommé (une seule chance,
    pas de re-proposition en boucle). Renvoie :
      • str non vide  = la question d'origine RÉÉCRITE avec la correction CONFIRMÉE -> à traiter normalement ;
      • ""            = refus/confirmation d'une demande de reformulation -> l'appelant invite à reformuler ;
      • None          = pas d'état en attente, ou réponse sans rapport -> traiter `texte` normalement.
    Sound : la substitution n'a lieu QUE sur confirmation explicite ; la question réécrite garde/retrouve son
    « ? » (une clarification confirmée EST une demande — faille « C'est noté » fermée)."""
    st = _EN_ATTENTE.pop(conv_id, None) if conv_id else None
    if not st or not isinstance(texte, str):
        return None
    tn = " ".join(_normalise(texte).split())
    if st.get("type") == "reformule":
        return "" if (_est_refus(tn) or _est_confirmation(tn)) else None
    if _est_refus(tn):
        return ""
    if _est_confirmation(tn) or tn == _normalise(st["proposition"]).strip():
        # 1) substitution sur le texte ORIGINAL (garde ponctuation/casse) ; 2) repli : texte normalisé.
        q2 = re.sub(rf"\b{re.escape(st['mot'])}\b", st["proposition"], st["question"], flags=re.IGNORECASE)
        if q2 == st["question"]:
            qn = _normalise(st["question"])
            q2 = re.sub(rf"\b{re.escape(st['mot'])}\b", st["proposition"], qn)
            if q2 == qn:
                return None
        if "?" not in q2:
            q2 += " ?"                                # une clarification confirmée est TOUJOURS une demande
        return q2
    return None


# ————————————————————————— ROUTAGE PAR BORNAGE APRÈS HORS (capacité 1) —————————————————————————
# Mots-outils à retirer pour extraire le SUJET de recherche (interrogatifs, déterminants, politesse, verbes creux).
_STOP_SUJET = frozenset(
    "quel quelle quels quelles qui que quoi qu ou comment combien quand pourquoi est sont etait sera ce cette "
    "ces cet le la les l un une des du de d au aux en dans sur sous pour par avec sans et puis donc alors "
    "dis dis-moi donne donnez sais peux pourrais saurais connais cherche trouve montre explique il elle on ne "
    "pas plus tu te toi moi je nous vous mon ma mes ton ta tes son sa ses stp svp bonjour merci fait faire "
    "veut veux dire signifie appelle situe lieu eu ete avoir etre y a t".split())

# Préfixes des textes de CE module (source unique -> la porte unique les reclasse POSITIVEMENT, capacité 3).
_PFX_HORS_FAIT = "Je n'ai pas ce fait vérifié en mémoire"
_PFX_NON_BORNE = "Question non bornée"
_PFX_INDECIDABLE = "Je n'arrive pas à rattacher ta demande"
_PFX_SATURATION = "Je ne sais pas encore traiter cette famille de demandes"
_PFX_PRECISER = "Peux-tu préciser le sujet"
_PFX_OPINION = "Il n'y a pas de réponse unique"     # cadrage subjectif de _reponse_opinion (= SUPPOSITION)

# Cache de JOIGNABILITÉ des sources (TTL) : le ping du registre est indépendant du sujet -> inutile (et lent :
# GET réels à chaque question inconnue du serveur plein) de re-contacter les sources à chaque tour.
_PING_TTL = 300.0
_PING_CACHE = None            # (t_monotonic, ok: bool, domaines: str, n: int)


def _sujet_recherche(question: str) -> str:
    """Mots de CONTENU de la question (normalisés, sans mots-outils) = le sujet à approfondir sur les sources.
    Extraction descriptive (pour la recherche et le message), jamais une réponse."""
    toks = [w for w in _normalise(question).split() if len(w) >= 3 and w not in _STOP_SUJET]
    return " ".join(toks[:8])


def _famille_non_borne(justification: str) -> str:
    m = re.search(r"pr[ée]dicat non-born[ée] \((\w+)\)", justification)
    return m.group(1).replace("_", " ") if m else "jugement/opinion"


def _ping_sources():
    """Joignabilité des sources de confiance (registre sources.py), avec cache TTL. Renvoie (ok, domaines, n)."""
    global _PING_CACHE
    with _VERROU:
        c = _PING_CACHE
    if c is not None and (time.monotonic() - c[0]) < _PING_TTL:
        return c[1], c[2], c[3]
    import veille as _VEI                                     # léger (atome + sources), paresseux
    res = _VEI.approfondit("joignabilité des sources de confiance", transport=_TRANSPORT)
    temoins = res.get("temoignages") or []
    ok = res.get("statut") == _VEI.OK and bool(temoins)
    doms = ", ".join(sorted({t.domaine for t in temoins}))
    with _VERROU:
        _PING_CACHE = (time.monotonic(), ok, doms, len(temoins))
    return ok, doms, len(temoins)


def _cherche_sources(question: str, c, conv_id=None) -> Reponse:
    """BORNÉ sans juge -> l'assistant CHERCHE LUI-MÊME côté sources de confiance (veille.py). HONNÊTETÉ STRICTE :
    v1 vérifie la JOIGNABILITÉ des sources du registre et le DIT tel quel — il ne prétend PAS y avoir cherché le
    sujet (l'extraction de faits depuis le web libre est refusée par veille.py, anti-hallucination). Tout reste
    SUPPOSITION RAPPORTÉE tant que non corroboré par un juge réel. Réseau réel = opt-in (IA_WEB=1, posé par le
    serveur d'interface) ou transport injecté (tests offline)."""
    sujet = _sujet_recherche(question)
    if not sujet or not any(len(t) >= 4 for t in sujet.split()):
        note_reformulation(conv_id)                           # « oui » au tour suivant -> invitation, pas « noté »
        return Reponse(CLARIFICATION,
                       f"{_PFX_PRECISER} de ta question — par exemple « population du Japon », "
                       f"« altitude du mont Blanc » ?", regime=c.regime, attente="sujet précis")
    if _TRANSPORT is None and os.environ.get("IA_WEB") != "1":
        return Reponse(HORS,
                       f"{_PFX_HORS_FAIT}. Une vérité existe (question bornée) : je pourrai la chercher sur mes "
                       f"sources de confiance quand ma recherche web sera activée — en attendant je m'abstiens "
                       f"plutôt que deviner.", regime=c.regime, source="recherche web désactivée (opt-in IA_WEB=1)")
    # RECHERCHE STRUCTURÉE — source FIABLE (Wikidata) -> réponse VÉRIFIÉE et ATTRIBUÉE (FAUX=0), avant le simple ping.
    # « source fiable = réponse véridique » (design Yohan) : extraction SPARQL déterministe, jamais du texte libre.
    try:
        import veille_structure as _VS
        _res = _VS.interroge_nl(question)
    except Exception:
        _res = None
    if _res:
        _a, _e, _valeur, _src = _res
        return Reponse(FAIT, f"{_valeur}  (trouvé sur {_src})", regime=c.regime,
                       source=f"{_src} — source structurée de confiance")
    # WEB LIBRE (Wikipédia) : rapport ATTRIBUÉ quand le structuré ne tranche pas (design Yohan « d'après [source] »).
    try:
        import veille_structure as _VS2
        _wl = _VS2.cherche_web_libre(question)
    except Exception:
        _wl = None
    if _wl:
        _extrait, _titre, _url = _wl
        try:                                   # GATE DE PERTINENCE (partagé avec repond._recherche_structuree) :
            _R = _module_repond()              # un extrait qui ne parle pas de la question n'est pas servi.
            if not getattr(_R, "_extrait_pertinent", lambda *a: True)(question, _titre, _extrait):
                _wl = None
        except Exception:
            pass
    if _wl:
        _extrait, _titre, _url = _wl
        return Reponse(SUPPOSITION, "D'après Wikipédia (« %s ») : %s" % (_titre, _extrait[:400]),
                       regime=c.regime, source="Wikipédia — %s (rapporté, non vérifié par Provara)" % _url)
    ok, doms, n = _ping_sources()
    if ok:
        return Reponse(HORS,
                       f"{_PFX_HORS_FAIT}. J'ai vérifié la joignabilité de {n} source(s) de confiance ({doms}) ; "
                       f"je ne sais pas encore y chercher « {sujet} » automatiquement — ça reste une piste à "
                       f"corroborer (supposition rapportée), pas un fait. Précise la question "
                       f"(ex. « capitale de X ») pour un lookup exact.", regime=c.regime, source=doms)
    return Reponse(HORS,
                   f"{_PFX_HORS_FAIT}, et mes sources de confiance sont injoignables pour le moment. "
                   f"Une vérité existe (question bornée) — je m'abstiens plutôt que deviner.", regime=c.regime)


def _reponse_opinion(question, c):
    """Question SUBJECTIVE : pas de réponse unique. On CADRE honnêtement (ça dépend du critère) et, si le web
    aide, on RAPPORTE des pistes ATTRIBUÉES (extrait Wikipédia) — jamais une vérité tranchée. Design Yohan :
    même sur du subjectif, proposer selon des critères objectifs + citer la source."""
    base = ("Il n'y a pas de réponse unique, c'est subjectif : ça dépend du critère (ventes, remplissage des "
            "salles, notoriété internationale, récompenses, influence…). Je ne tranche donc pas.")
    if os.environ.get("IA_WEB") == "1" or _TRANSPORT is not None:
        try:
            import veille_structure as _VS
            wl = _VS.cherche_web_libre(question)
        except Exception:
            wl = None
        if wl:
            extrait, titre, url = wl
            return Reponse(SUPPOSITION,
                           base + " Pour te donner des pistes, d'après Wikipédia (« %s ») : %s" % (titre, extrait[:360]),
                           regime=c.regime, source="Wikipédia — %s (rapporté, non vérifié par Provara)" % url)
    return Reponse(SUPPOSITION, base + " Donne-moi un critère objectif (ventes, récompenses…) et je cherche.",
                   regime=c.regime)


def apres_hors(question: str, conv_id=None) -> Reponse | None:
    """Cerveau APRÈS-HORS : la cascade factuelle vérifiée et la mémoire de dialogue n'ont RIEN rendu.
    Router par le gardien de bornage plutôt que l'aveu générique — sans JAMAIS fabriquer un fait :
      • régime FAIT (seul juge interne : calcul arithmétique réellement évalué, COUVRANT toute la question) ;
      • NON-BORNÉ -> cadrage honnête (pas de fait à trancher) ;
      • BORNÉ sans juge -> recherche autonome côté sources de confiance (HORS honnête + provenance) ;
      • INDÉCIDABLE -> QUESTION DE CLARIFICATION (2 fois de suite max, puis HORS différencié — anti-boucle).
    Renvoie une Reponse, ou None (l'appelant garde son repli existant)."""
    q = (question or "").strip()
    if not q:
        return None
    try:
        c = _CB.classe(q)
    except ValueError:
        return None
    rep = None
    if c.regime == _CB.R_FAIT:
        val = _CB._juge_arith(_CB._norm(q))                  # même juge que le classement (recalcul déterministe)
        if val is not None:
            if isinstance(val, float) and val.is_integer():
                val = int(val)
            rep = Reponse(FAIT, str(val), regime=c.regime, source="calcul arithmétique (AST évalué, couvrant)")
    elif c.statut_ontologique == _CB.NON_BORNE:
        rep = _reponse_opinion(q, c)
    elif c.statut_ontologique == _CB.BORNE:
        rep = _cherche_sources(q, c, conv_id)
    else:                                                    # indécidable -> demander, jamais deviner
        n = _INDECIS.get(conv_id, 0) + 1 if conv_id else 1
        if conv_id:
            _INDECIS[conv_id] = n
        note_reformulation(conv_id)
        if n >= 3:                                           # anti-boucle : ne pas répéter la même question
            rep = Reponse(HORS,
                          f"{_PFX_SATURATION} — essaie un fait précis (« capitale de X », « population de Y », "
                          f"« définition de Z ») ou un calcul, et je réponds avec du vérifié.",
                          regime=c.regime)
        else:
            rep = Reponse(CLARIFICATION,
                          f"{_PFX_INDECIDABLE} à un fait vérifiable. Peux-tu préciser le sujet et l'attribut "
                          f"voulu — par exemple « capitale de l'Espagne », « population du Japon », "
                          f"« définition de sérendipité » ?", regime=c.regime, attente="reformulation précise")
    if conv_id and rep is not None and rep.statut != CLARIFICATION and c.statut_ontologique != _CB.INDECIDABLE:
        _INDECIS.pop(conv_id, None)                          # une issue non-indécidable remet le compteur à zéro
    return rep


def complement(question: str, conv_id=None):
    """Étage APRÈS-HORS pour interface/repond.py : le TEXTE à afficher (str) ou None (-> repli existant).
    La porte unique reclasse ces textes par leurs préfixes (classification POSITIVE, cf. qualifie_texte)."""
    rep = apres_hors(question, conv_id)
    return rep.texte if rep is not None and rep.texte else None


# ————————————————————————— PORTE UNIQUE (capacité 3) — ia.assistant(question) —————————————————————————
_REPOND_MOD = None
_VERROU_MOD = threading.Lock()


def _module_repond():
    """interface/repond.py chargé UNE SEULE fois — réutilise l'instance du serveur si elle existe (sys.modules)
    pour qu'états multi-tours et caches soient PARTAGÉS entre les deux portes (faille double-module fermée).
    Verrouillé (double-checked) contre la double init concurrente."""
    global _REPOND_MOD
    if _REPOND_MOD is not None:
        return _REPOND_MOD
    with _VERROU_MOD:
        if _REPOND_MOD is not None:
            return _REPOND_MOD
        import sys as _sys
        import importlib.util
        deja = _sys.modules.get("repond")
        if deja is not None and hasattr(deja, "est_fallback"):
            _REPOND_MOD = deja                               # instance du serveur/validateur : on la partage
            return _REPOND_MOD                               # (quel que soit son chemin : layout src/ ou gelé .exe)
        # Layouts possibles : harnais (interface/ sous _ICI) et Provara (interface/ FRÈRE de src/). L'ancien chemin
        # unique src/interface/repond.py n'existait pas -> FileNotFoundError avalée par les appelants = étage
        # clarification MORT en silence dans le produit.
        for base in (_ICI, os.path.dirname(_ICI)):
            chemin = os.path.abspath(os.path.join(base, "interface", "repond.py"))
            if not os.path.exists(chemin):
                continue
            spec = importlib.util.spec_from_file_location("interface_repond", chemin)
            mod = importlib.util.module_from_spec(spec)
            _sys.modules["interface_repond"] = mod
            spec.loader.exec_module(mod)
            _sys.modules.setdefault("repond", mod)           # un `import repond` ultérieur partage l'instance
            _REPOND_MOD = mod
            return _REPOND_MOD
        import repond as mod                                 # .exe gelé : le module bundlé se résout par l'import
        _REPOND_MOD = mod
        return _REPOND_MOD


def qualifie_texte(texte: str) -> Reponse | None:
    """Classification POSITIVE d'un texte du pipeline : chaque texte terminal NON-FACTUEL est reconnu par sa
    constante/son préfixe et reçoit son vrai statut. Renvoie None si le texte n'est pas un terminal connu
    (-> il vient d'un étage FACTUEL vérifié). JAMAIS de défaut « fait » pour un texte non identifié non-factuel."""
    if not isinstance(texte, str) or not texte:
        return None
    R = _module_repond()
    if R.est_fallback(texte):
        return Reponse(HORS, texte)
    _refus = getattr(R, "_MSG_REFUS", None)
    try:                                                     # les refus sont VARIÉS par formulation.py : reconnaître
        _refus_tous = set(R._variantes("refus", _refus))     # toute la famille, pas seulement le libellé historique
    except Exception:
        _refus_tous = set()
    if texte == _refus or texte in _refus_tous:
        return Reponse(CLARIFICATION, texte, attente="reformulation")
    if texte.startswith(getattr(R, "_MSG_RAPPEL_PREFIXE", "D'après ce que tu m'as dit : ")):
        return Reponse(SUPPOSITION, texte,
                       source="mémoire de dialogue (énoncé utilisateur RAPPORTÉ verbatim, contenu non vérifié)")
    if texte.startswith(getattr(R, "_MSG_DYM_PREFIXE", "Je ne suis pas sûr du mot « ")):
        return Reponse(CLARIFICATION, texte, attente="confirmer (oui/non) ou reformuler")
    if texte.startswith(_PFX_HORS_FAIT):
        return Reponse(HORS, texte, regime=_CB.R_SUPPOSITION_A_CHERCHER)
    if texte.startswith(_PFX_NON_BORNE) or texte.startswith(_PFX_OPINION):
        return Reponse(SUPPOSITION, texte, regime=_CB.R_SUPPOSITION_OPINION)
    if texte.startswith(_PFX_INDECIDABLE) or texte.startswith(_PFX_PRECISER):
        return Reponse(CLARIFICATION, texte, attente="reformulation précise")
    if texte.startswith(_PFX_SATURATION):
        return Reponse(HORS, texte)
    return None


def repond(question: str, conv_id=None, *, pleine: bool = True, memoire=None) -> Reponse:
    """PORTE CONVERSATIONNELLE UNIQUE : comprend la question (pipeline existant), répond depuis le vérifié,
    calcule, cherche elle-même (bornage -> sources de confiance), et POSE une question de clarification quand la
    demande est ambiguë. Renvoie TOUJOURS une Reponse — jamais une devinette.
    NB : ne dépose RIEN dans la mémoire de conversation (l'appelant décide) ; `pleine=False` = mode léger sans
    lecteur (dialogue/mémoire seulement) ; `memoire` = MemoireConversation injectable (tests isolés), défaut =
    le singleton partagé ; sans `conv_id`, un id JETABLE est utilisé (pas de multi-tours ni de clarification
    différée sans conversation explicite — et aucun état partagé entre appelants anonymes)."""
    q = (question or "").strip()
    if not q:
        return Reponse(HORS, "")
    conv = conv_id or f"_porte_{next(_CPT)}"
    R = _module_repond()
    if memoire is None:
        import conversation                                   # léger, paresseux
        memoire = conversation.MEMOIRE
    out = R.repond(memoire, conv, q, pleine=pleine)
    if not out:
        return Reponse(HORS, "")
    try:                                                      # social/méta -> échange (pas un fait)
        if R._politesse(q) == out or R._meta_assistant(q) == out:
            return Reponse(ECHANGE, out)
    except Exception:
        pass
    env = qualifie_texte(out)
    if env is not None:
        return env
    # Texte NON terminal-connu = produit par un étage FACTUEL du pipeline (lookup vérifié / raisonnement /
    # oui-non / listes / fiche / multi-tours / calcul) : le lecteur A tranché -> rebouclage légitime du verdict.
    try:
        regime = _CB.classe(q, juge_verdict=True, juge_nom="lecteur").regime
    except ValueError:
        regime = ""
    return Reponse(FAIT, out, regime=regime, source="pipeline vérifié (lecteur/raisonnement/calcul)")
