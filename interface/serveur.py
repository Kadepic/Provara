#!/usr/bin/env python3
"""
INTERFACE LOCALE — petit serveur web souverain par-dessus la mémoire de conversation.

But (v1, volontairement minimal — cf. harnais/BRIEF_T3_INTERFACE.md) : DEUX fonctions seulement,
  1. retrouver / voir l'historique des conversations (liste + tous les tours, VERBATIM, dans l'ordre) ;
  2. créer une nouvelle conversation et y écrire des messages.

Forme : bibliothèque STANDARD uniquement (`http.server`). Zéro framework, zéro Node, zéro build, zéro
dépendance. Localhost UNIQUEMENT (souverain : les données ne quittent jamais la machine — pilier du projet).

Architecture (pensée pour l'évolution, sans sur-ingénierie) :
  • le STOCKAGE n'est PAS réimplémenté ici : on appelle l'API de `conversation.MEMOIRE` (JSONL durable, scope,
    RGPD). Ce fichier n'est qu'un mince wrapper JSON + service de la page.
  • IMPORTANT — légèreté : on importe `conversation` (≈ 13 Mo RSS), JAMAIS `ia` (qui chargerait le lecteur,
    622 Mo → risque OOM en parallèle de T1/T2). « Parler à la vraie IA » est une évolution future : un hook
    propre est laissé plus bas (_repond_ia), commenté, NON branché.



  • une simple TABLE DE ROUTES (méthode, chemin) -> handler : ajouter un panneau plus tard = une ligne + un
    bout de HTML. Pas d'abstraction prématurée.

Soundness / honnêteté (même esprit que tout le projet) : on n'affiche QUE des tours réellement stockés
(verbatim). Jamais d'invention, jamais de reformulation. États vides explicites.
"""
from __future__ import annotations

import json
import os
import re
import socket
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

# Le module de stockage vit dans le dossier parent (harnais/). On l'ajoute au path SANS rien y écrire.
_ICI = os.path.dirname(os.path.abspath(__file__))
_HARNAIS = os.path.dirname(_ICI)
if _HARNAIS not in sys.path:
    sys.path.insert(0, _HARNAIS)
import verax_boot  # noqa: E402  -- met src/ (conversation, ia, ...) sur sys.path

import conversation  # noqa: E402  (léger ; n'importe PAS `ia`)
import repond        # noqa: E402  (léger ; l'étage IA lourd est en import PARESSEUX, opt-in)

_HTML = os.path.join(_ICI, "index.html")

# DOCUMENTS ATTACHÉS par conversation (upload PDF/texte) : conv_id -> lecteur_document.Document. Source de REPLI
# attribuée — quand la connaissance vérifiée et le web n'ont rien, on répond depuis le document importé (passage
# VERBATIM + page). En mémoire de session (reconstruit à l'upload) ; jamais envoyé ailleurs (souverain).
_DOCS: dict = {}

# DONNÉES STRUCTURÉES attachées par conversation (upload CSV/TSV/JSON) : conv_id -> interroge_donnees.Tableau|Arbre.
# Route 3 (2026-07-09) : le document structuré n'est plus seulement LU, il est INTERROGEABLE (max/min/somme/
# moyenne d'une colonne, comptages, extraction de cellule/clé — opérations EXACTES, preuve de localisation).
_DONNEES: dict = {}


def _document_de(conv_id: str):
    return _DOCS.get(conv_id)


# FAITS PERSONNELS confiés par l'utilisateur (« le chien s'appelle Rex ») : conv_id -> faits_conversation.
# FaitsConversation, REJOUÉ depuis les tours stockés (zéro stockage nouveau ; RGPD : purgé avec la conversation).
_FAITS_CONV: dict = {}

# LE FIL (chantier compréhension 2026-07-09) : conv_id -> situation.Situation — tout ce que l'utilisateur
# AFFIRME (clauses verbatim, grandeurs typées, hypothèses étiquetées), rejoué des tours. Sert « résume notre
# conversation », « reprends ce que je t'ai dit sur X », « quelles données je t'ai données ? » — et le PONT
# grandeurs→moteurs à venir.
_SITUATIONS: dict = {}


def _situation_de(memoire, conv_id: str):
    sit = _SITUATIONS.get(conv_id)
    if sit is None:
        import situation
        sit = situation.depuis_tours(memoire.tours.get(conv_id, []))
        _SITUATIONS[conv_id] = sit
    return sit


def _faits_de(memoire, conv_id: str):
    """État des faits personnels d'une conversation (cache par conv, rejoué des tours au premier accès —
    appelé AVANT le stockage du message courant, qui est ensuite appris incrémentalement)."""
    fc = _FAITS_CONV.get(conv_id)
    if fc is None:
        import faits_conversation
        fc = faits_conversation.depuis_tours(memoire.tours.get(conv_id, []))
        _FAITS_CONV[conv_id] = fc
    return fc

# IA pleine (étage 2 de repond.py) : ACTIVE PAR DÉFAUT (l'utilisateur veut tester l'IA réelle). Le lecteur
# (~622 Mo) est chargé PARESSEUSEMENT à la première question (pas au démarrage). Pour forcer le mode léger
# (mémoire de dialogue seule, sans charger le lecteur), lancer avec IA_LEGER=1.
# ⚠️ Cohabitation : éviter de lancer en mode plein PENDANT qu'un autre process lourd charge le lecteur (OOM WSL).
_IA_PLEINE = os.environ.get("IA_LEGER") != "1"


# ══════════════════════════════════════════════════════════════════════════════
#  ÉTAT DE CHARGEMENT + INSTALLATION OPTIONNELLE DE LA BASE COMPLÈTE (72M faits)
#  Pilote la modale d'interface : elle s'affiche tant que `pret=False`, montre la
#  progression d'un éventuel téléchargement, et disparaît quand l'IA est prête.
# ══════════════════════════════════════════════════════════════════════════════
import sys as _sys
import threading as _threading
_STATUT_LOCK = _threading.Lock()
_STATUT = {"pret": False, "phase": "chargement", "detail": "Chargement de la connaissance…",
           "pct": None, "installation": False, "redemarrage": False, "erreur": "", "maj_appli": False}


def _maj_statut(**kw):
    with _STATUT_LOCK:
        _STATUT.update(kw)


def statut_chargement():
    """État courant pour la modale (léger, sans charger le lecteur). Inclut si la base complète est déjà là."""
    with _STATUT_LOCK:
        s = dict(_STATUT)
    try:
        import telecharge_donnees
        s["base_complete"] = telecharge_donnees.base_complete_presente()
    except Exception:
        s["base_complete"] = False
    s["installable"] = not s["base_complete"]     # on propose l'install tant que la base complète n'est pas là
    return s


def _installer_base(*_a):
    """Déclenche le téléchargement + installation de la base complète (72M) EN TÂCHE DE FOND. Idempotent."""
    with _STATUT_LOCK:
        if _STATUT.get("installation"):
            return {"ok": True, "deja": True}
        _STATUT.update(installation=True, redemarrage=False, phase="telechargement",
                       detail="Démarrage de l'installation…", pct=0, erreur="")

    def _run():
        try:
            import telecharge_donnees as td
            if td.assure_base_complete(notifier=_maj_statut):
                td.assure_cache_complet(notifier=_maj_statut)     # best-effort : index pré-construit
                _maj_statut(phase="installee", pct=100, installation=False, redemarrage=True,
                            detail="Base complète installée. Redémarre Provara pour l'activer.")
            else:
                _maj_statut(phase="erreur", installation=False, erreur="echec",
                            detail="Le téléchargement a échoué (réseau ?). Tu peux réessayer plus tard.")
        except Exception as e:
            _maj_statut(phase="erreur", installation=False, erreur=str(e),
                        detail="Installation impossible : %s" % e)
    _threading.Thread(target=_run, daemon=True).start()
    return {"ok": True, "demarre": True}


def _quitter(*_a):
    """Arrête Provara proprement. Utile en mode FENÊTRÉ (.exe sans console -> plus de Ctrl+C)."""
    def _q():
        import time
        time.sleep(0.4)                          # laisse la réponse HTTP partir
        os._exit(0)
    _threading.Thread(target=_q, daemon=True).start()
    return {"ok": True}


def _redemarrer(*_a):
    """Relance le process (pour activer la base complète fraîchement installée). Best-effort."""
    def _re():
        import time
        time.sleep(0.7)                          # laisse le temps de renvoyer la réponse HTTP
        try:
            if getattr(_sys, "frozen", False):
                os.execv(_sys.executable, [_sys.executable])
            else:
                os.execv(_sys.executable, [_sys.executable] + _sys.argv)
        except Exception:
            os._exit(0)
    _threading.Thread(target=_re, daemon=True).start()
    return {"ok": True}


# ————————————————————————————————— ARCHIVAGE UI (≠ effacement RGPD) —————————————————————————————————
# Deux notions DISTINCTES de « suppression », à ne pas confondre :
#   • ARCHIVER (ce bloc) : RETIRER de l'historique affiché, MAIS garder les données -> l'IA S'EN SOUVIENT
#     toujours (rappelle() voit encore les tours). C'est ce que veut l'utilisateur : « même si la conversation
#     n'est plus dispo en UI, l'IA doit pouvoir s'en souvenir ». On ne touche PAS conversation.py : on tient
#     juste, à CÔTÉ du stock (sidecar `_archive_ui.json` dans la même `racine`), la liste des id masqués.
#   • OUBLIER (oublie_conversation) : effacement RGPD RÉEL (mémoire + index + disque) -> l'IA NE s'en souvient
#     PLUS. Action forte, séparée, volontaire.

def _chemin_archive(memoire) -> str | None:
    return os.path.join(memoire.racine, "_archive_ui.json") if getattr(memoire, "racine", None) else None


def _lit_archive(memoire) -> set:
    p = _chemin_archive(memoire)
    if not p or not os.path.exists(p):
        return set()
    try:
        with open(p, encoding="utf-8") as fh:
            return set(json.load(fh))
    except (OSError, ValueError):
        return set()


def _ecrit_archive(memoire, ids: set) -> None:
    p = _chemin_archive(memoire)
    if not p:
        return
    os.makedirs(memoire.racine, exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(sorted(ids), fh, ensure_ascii=False)


# ————————————————————————————————— LOGIQUE (mince wrapper sur conversation.MEMOIRE) —————————————————————————————————
# Cette couche traduit les appels HTTP en appels d'API et renvoie des dicts JSON-sérialisables. Elle ne
# connaît rien du protocole HTTP : testable directement (cf. valide_interface.py), réutilisable ailleurs.

def liste_conversations(memoire, inclure_archivees: bool = False) -> dict:
    """Conversations à AFFICHER : tout ce qui existe réellement, MOINS les archivées (masquées de l'historique
    mais conservées pour la mémoire de l'IA). `inclure_archivees=True` les renvoie aussi (avec `archivee=True`),
    pour un futur panneau « archives »."""
    arch = _lit_archive(memoire)
    items = []
    for cid in memoire.conversations():            # scope=None -> tout ce qui existe réellement sur le disque
        if cid in arch and not inclure_archivees:
            continue
        items.append({
            "id": cid,
            "scope": memoire.scope.get(cid, "prive"),
            "n": len(memoire.reprend(cid)),
            "archivee": cid in arch,
        })
    return {"items": items}


def archive_conversation(memoire, conv_id: str) -> dict:
    """Retire une conversation de l'historique affiché SANS effacer ses données : l'IA continue de s'en souvenir
    (rappelle la voit toujours). Réversible (desarchive_conversation)."""
    cid = str(conv_id)
    arch = _lit_archive(memoire)
    arch.add(cid)
    _ecrit_archive(memoire, arch)
    return {"ok": True, "archivee": True, "id": cid}


def desarchive_conversation(memoire, conv_id: str) -> dict:
    """Re-affiche une conversation archivée (les données n'avaient jamais bougé)."""
    arch = _lit_archive(memoire)
    arch.discard(str(conv_id))
    _ecrit_archive(memoire, arch)
    return {"ok": True, "archivee": False, "id": str(conv_id)}


def lire_conversation(memoire, conv_id: str) -> dict:
    """Tous les tours d'une conversation, VERBATIM, dans l'ordre. Conversation inconnue -> tours vides (état
    vide honnête, pas une erreur : l'utilisateur vient peut-être d'en créer une encore sans message)."""
    tours = memoire.reprend(conv_id)               # [] si inconnue/vide — aucune invention
    return {
        "id": conv_id,
        "scope": memoire.scope.get(conv_id, "prive"),
        "tours": [{"seq": t["seq"], "role": t["role"], "texte": t["texte"], "ts": t["ts"]} for t in tours],
    }


def ajoute_message(memoire, conv_id: str, texte: str, scope: str = "prive", pleine: bool = False) -> dict:
    """Enregistre le message de l'utilisateur (tour role='user'), génère une réponse SOUND (tour role='ia') et
    renvoie l'état relu (verbatim). Texte vide -> refusé proprement (le stockage l'ignore, seq=-1).

    Ordre IMPORTANT pour la soundness : on calcule la réponse AVANT d'indexer la question, sinon l'assistant
    pourrait se citer sa propre question. La réponse ne sort JAMAIS de la mémoire réelle (cf. repond.py)."""
    if not str(texte).strip():
        return {"ok": False, "raison": "message vide", **lire_conversation(memoire, conv_id)}
    arch = _lit_archive(memoire)                                     # écrire dans une conv archivée la fait réapparaître
    if conv_id in arch:
        arch.discard(conv_id)
        _ecrit_archive(memoire, arch)
    #   FAITS PERSONNELS (extraction, 2026-07-09) : « le chien s'appelle Rex » -> fait INTERROGEABLE ; « comment
    #   s'appelle le chien ? » -> réponse ATTRIBUÉE ; « en fait c'est Max » (sous focus) -> correction d'AUTORITÉ
    #   sans exigence de source (sur SA vie, l'utilisateur EST la source — ≠ faits-monde ci-dessous). AVANT la
    #   correction-monde : motifs fermés, zéro capture d'une question générale (sujet inconnu -> None).
    try:
        _fc = _faits_de(memoire, conv_id)
        _res_fc = _fc.apprend(texte)
        _rep_fc = _fc.accuse(_res_fc) if _res_fc else _fc.repond(texte)
    except Exception:
        _rep_fc = None
    #   LE FIL (situation) : apprend CHAQUE tour utilisateur ; répond sur ses motifs fermés (« résume notre
    #   conversation », « reprends ce que je t'ai dit sur X », « quelles données je t'ai données ? »).
    try:
        _sit = _situation_de(memoire, conv_id)
        _seq_prochain = len(memoire.tours.get(conv_id, [])) + 1
        _n_sit = _sit.apprend(_seq_prochain, texte)
        if not _rep_fc:
            _rep_fc = _sit.repond(texte)
        if not _rep_fc:
            import pont_grandeurs                    # PONT : les grandeurs énoncées deviennent des opérandes
            _rep_fc = pont_grandeurs.repond(texte, _sit)
            if not _rep_fc:                          # « pourquoi ? » NU -> mécanisme de la dernière réponse du pont
                _rep_fc = pont_grandeurs.pourquoi_dernier(texte, _DERNIERE_REPONSE.get(conv_id), _sit)
        # déclaration TECHNIQUE (grandeurs, pas de question) -> accusé du FIL, à la place du lookup fragmenté
        # « je ne l'ai pas encore en mémoire » ×N (vécu sonde échangeur). Les affirmations sans grandeur
        # gardent leurs flux existants (mémo, attunement, apprentissage de patrons).
        # …MAIS un ORDRE n'est pas une déclaration (correctif 2026-07-12). « Convertis 5 km en mètres »
        # porte une grandeur et aucun « ? » : le fil l'accusait en « C'est noté, je tiens le fil : 5 km ».
        # C'est exactement le faux que `repond._est_demande_imperative` interdit DÉJÀ en fin de cascade —
        # mais le fil répondait AVANT elle. Une même règle, appliquée à un seul endroit, laissait passer
        # l'autre. On la consulte donc ici aussi : ordre -> on rend la main au pipeline (calcul, puis repli
        # honnête). Sound : ne change que le ROUTAGE, jamais un fait.
        if not _rep_fc and _n_sit and "?" not in texte and not repond._est_demande_imperative(texte):
            _rep_fc = _sit.accuse_tour(_seq_prochain)
    except Exception:
        pass
    if _rep_fc:
        seq = memoire.ajoute(conv_id, "user", texte, scope=scope)
        memoire.ajoute(conv_id, "ia", _rep_fc, scope=scope)
        _DERNIERE_QUESTION[conv_id] = texte            # « prouve-le » au tour suivant doit retrouver cet échange
        _DERNIERE_REPONSE[conv_id] = _rep_fc
        return {"ok": seq >= 0, "seq": seq, "reponse": _rep_fc, **lire_conversation(memoire, conv_id)}
    #   « PROUVE-LE » (audit item 11, 2026-07-09) : « es-tu sûr ? », « ta source ? » -> production de PREUVE sur
    #   la dernière réponse (chaîne de composition, liens attribués, re-dérivation + source de table) ; type de
    #   réponse improuvable -> on le DIT (jamais une justification fabriquée).
    if repond.est_demande_preuve(texte):
        q0, r0 = _DERNIERE_QUESTION.get(conv_id), _DERNIERE_REPONSE.get(conv_id)
        if r0 and "toi qui me l'as dit" in r0:
            rep_p = ("La preuve est dans cette conversation même : c'est TOI qui me l'as dit, je n'ai fait que "
                     "le retenir (relis tes messages plus haut). Si c'est faux, corrige-moi — ta correction "
                     "fait autorité.")
        else:
            rep_p = repond.preuve_de(q0, r0) if (q0 and r0) else None
        if rep_p is None:
            rep_p = ("Honnêtement : je ne sais pas produire de preuve formelle pour %s Ma règle reste FAUX=0 : "
                     "fait vérifié, rapport attribué à sa source, ou abstention — jamais une justification "
                     "fabriquée. Repose la question et demande-moi la preuve juste après : je te montrerai "
                     "d'où vient chaque élément." %
                     ("cette réponse-là." if r0 else "l'instant (je ne retrouve pas de réponse récente à prouver)."))
        seq = memoire.ajoute(conv_id, "user", texte, scope=scope)
        memoire.ajoute(conv_id, "ia", rep_p, scope=scope)
        return {"ok": seq >= 0, "seq": seq, "reponse": rep_p, **lire_conversation(memoire, conv_id)}
    #   CORRECTION UTILISATEUR (AUTORITÉ) : « c'est faux, c'est X » / « non, la réponse est X » se rapporte à la
    #   DERNIÈRE question factuelle -> on enregistre la correction (l'utilisateur juge la réalité). FAUX=0 :
    #   simple mémorisation de SA réponse, ré-appliquée telle quelle et attribuée ensuite.
    _corr = _capture_correction(conv_id, texte)
    if _corr:
        seq = memoire.ajoute(conv_id, "user", texte, scope=scope)
        memoire.ajoute(conv_id, "ia", _corr, scope=scope)
        return {"ok": seq >= 0, "seq": seq, "reponse": _corr, **lire_conversation(memoire, conv_id)}
    seq = memoire.ajoute(conv_id, "user", texte, scope=scope)        # STOCKE D'ABORD : jamais perdu, jamais bloqué
    # DONNÉES STRUCTURÉES ATTACHÉES (Route 3) : les opérations sur le CSV/JSON importé passent AVANT le pipeline —
    # elles sont CHIRURGICALES (ne répondent que si la question nomme les colonnes/clés/valeurs RÉELLES du fichier,
    # ou ses lignes/colonnes) et attribuées au fichier. Vécu e2e : « combien de lignes ? » partait au lexique
    # (« 18 termes classés ligne ») au lieu du CSV attaché. Le document TEXTE, lui, reste en repli d'abstention.
    reponse = None
    if _DONNEES.get(conv_id) is not None:
        try:
            import interroge_donnees
            reponse = interroge_donnees.repond(texte, _DONNEES[conv_id])
        except Exception:
            reponse = None
    # La réponse filtre déjà le message courant (texte != courant) -> pas d'auto-citation malgré l'indexation.
    if not reponse:
        reponse = repond.repond(memoire, conv_id, texte, pleine=pleine)
    # DOCUMENT ATTACHÉ : si la connaissance vérifiée/le web n'ont RIEN donné (repli honnête) et qu'un document
    # est importé dans cette conversation, on répond depuis LUI (passage VERBATIM + page). Le document ne
    # détourne jamais une bonne réponse — il ne parle que quand l'IA allait dire « je ne sais pas ».
    rep_doc = _reponse_document(conv_id, texte) if _est_abstention(reponse) else None
    if rep_doc:
        reponse = rep_doc
    # APPRENTISSAGE DE PATRONS : si le tour PRÉCÉDENT de l'utilisateur a été une ABSTENTION et que CE message
    # RÉUSSIT (réponse non-abstention), on apprend « formulation ratée -> formulation qui marche » (même sujet
    # exigé côté module). Sound : n'apprend qu'un ré-aiguillage de formulation, jamais un fait.
    if reponse and not _est_abstention(reponse):
        _apprend_reformulation(conv_id, memoire, texte)
    _DERNIER_ECHEC[conv_id] = texte if _est_abstention(reponse) else None
    # mémorise la dernière QUESTION (pour qu'une correction « c'est faux, c'est X » au tour suivant sache quoi
    # corriger) : une demande qui a produit une réponse, hors interjection/correction.
    if reponse and len(texte.split()) >= 2:
        _DERNIERE_QUESTION[conv_id] = texte
        _DERNIERE_REPONSE[conv_id] = reponse            # pour citer « j'avais X » quand l'utilisateur corrige
    if reponse:
        memoire.ajoute(conv_id, "ia", reponse, scope=scope)          # réponse sound, durable, verbatim
    return {"ok": seq >= 0, "seq": seq, "reponse": reponse, **lire_conversation(memoire, conv_id)}


_DERNIER_ECHEC: dict = {}   # conv_id -> dernier message utilisateur resté SANS réponse (abstention), ou None
_DERNIERE_QUESTION: dict = {}   # conv_id -> dernière question factuelle posée par l'utilisateur (pour corriger)
_DERNIERE_REPONSE: dict = {}    # conv_id -> réponse de Provara à cette question (pour la citer quand on challenge)
_CORRECTION_ATTENTE: dict = {}  # conv_id -> {"question", "valeur"} : correction en attente d'une SOURCE

_RE_CORRECTION = re.compile(
    r"^\s*(?:non\b[,.! ]*)?(?:c'?est faux|c'?est inexact|t'?as tort|tu te trompes|erreur|faux)\b[,.: ]*"
    r"(?:c'?est|la (?:bonne )?r[ée]ponse est|en (?:fait|vrai) c'?est|il s'?agit de|c'?[ée]tait)?\s*(.+?)\s*[.?!]*$",
    re.I)
_RE_CORRECTION2 = re.compile(
    r"^\s*(?:non|mais non)\b[,.! ]+(?:c'?est|la r[ée]ponse est|en fait c'?est)\s+(.+?)\s*[.?!]*$", re.I)
# une source citée dans le message : lien, domaine, ou mot-clé de référence + contenu
_RE_SOURCE = re.compile(
    r"https?://\S+|www\.\S+|\b[a-z0-9\-]+\.(?:fr|com|org|net|edu|gov|be|ch|ca|io|info)\b|"
    r"\b(?:d'?apr[èe]s|selon|source\s*[:=]?|r[ée]f[ée]rence|wikip[ée]dia|wikidata|larousse|encyclop[ée]die|"
    r"le\s+livre|l'?ouvrage|la\s+constitution|l'?article)\b", re.I)


def _extrait_source(texte: str):
    """Extrait la source citée d'un message (lien/domaine/référence), ou None si aucune source crédible."""
    if _RE_SOURCE.search(texte):
        return " ".join(texte.split())[:200]
    return None


def _valeur_correction(texte: str):
    """La valeur proposée dans « c'est faux, c'est X » (X, sans la source éventuelle), ou None."""
    m = _RE_CORRECTION.match(texte) or _RE_CORRECTION2.match(texte)
    if not m:
        return None
    val = (m.group(1) or "").strip(" .?!\"'«»")
    # retire une éventuelle source en fin (« Sucre, d'après la constitution ») pour ne garder que la valeur
    val = re.split(r"\s*[,;]\s*(?:d'?apr[èe]s|selon|source|car|parce)", val, 1, re.I)[0].strip(" .?!\"'«»")
    if 1 <= len(val.split()) <= 12:
        return val
    return None


def _capture_correction(conv_id: str, texte: str):
    """Gère les corrections utilisateur EXIGEANT une source (FAUX=0 : pas d'écrasement de vérité sur simple
    affirmation). Renvoie un message (str) si le tour EST une correction / une source attendue, sinon None.
      1. correction NUE (« c'est faux, c'est X ») -> Provara CHALLENGE : cite sa réponse et demande la source ;
      2. correction AVEC source (« c'est X, d'après <src> ») -> enregistrée + attribuée ;
      3. la source arrive au tour SUIVANT (état en attente) -> enregistrée."""
    import confiance
    # (2ter) une source qui répond à un challenge en attente
    attente = _CORRECTION_ATTENTE.get(conv_id)
    if attente:
        src = _extrait_source(texte)
        if src:
            confiance.corrige(attente["question"], attente["valeur"], src)
            _CORRECTION_ATTENTE[conv_id] = None
            return ("Merci, je retiens « %s » : « %s » — d'après la source que tu m'indiques (%s). Je la citerai "
                    "quand tu reposeras la question." % (attente["question"], attente["valeur"], src))
        # pas encore de source -> on redemande UNE fois, sans harceler
        if re.search(r"\b(je sais|c'?est comme|crois[- ]?moi|point final|puisque je te le dis)\b", texte, re.I):
            _CORRECTION_ATTENTE[conv_id] = None
            return ("Sans source vérifiable, je préfère ne pas modifier une information — je m'en tiens à ce que "
                    "je peux vérifier. Reviens avec une référence (un lien, un ouvrage) et je l'enregistrerai.")
        return None
    # (2) une correction dans ce message
    val = _valeur_correction(texte)
    if not val:
        return None
    q = _DERNIERE_QUESTION.get(conv_id)
    if not q:
        return None
    src = _extrait_source(texte)
    if src:                                              # correction SOURCÉE d'emblée -> enregistrée + attribuée
        confiance.corrige(q, val, src)
        return ("Merci, je retiens « %s » : « %s » — d'après la source que tu m'indiques (%s)." % (q, val, src))
    # correction NUE -> CHALLENGE : cite ce que Provara avait, exige une source pour modifier
    _CORRECTION_ATTENTE[conv_id] = {"question": q, "valeur": val}
    avait = _DERNIERE_REPONSE.get(conv_id)
    prefixe = ("J'avais « %s ». " % avait[:120]) if avait else ""
    return (prefixe + "Pour que je retienne « %s » à la place, sur quelle SOURCE t'appuies-tu ? (un lien, un "
            "ouvrage, une référence) — je ne modifie pas une information sans source vérifiable." % val)


def _apprend_reformulation(conv_id: str, memoire, texte_reussi: str) -> None:
    """Si le message précédent de cette conversation était une abstention, apprends l'alias échec->réussite."""
    echec = _DERNIER_ECHEC.get(conv_id)
    if not echec or echec.strip() == texte_reussi.strip():
        return
    try:
        import apprentissage_patrons
        apprentissage_patrons.enregistre(echec, texte_reussi)
    except Exception:
        pass


def _est_abstention(reponse: str) -> bool:
    """La réponse du routeur est-elle un aveu d'ignorance (pas une vraie réponse) ? -> alors on peut consulter
    le document attaché. Couvre : vide, replis de repond.py (est_fallback), ET les messages d'assistant_nl
    (indécidable/saturation) qui, en mode plein, remplacent le repli simple mais restent des non-réponses."""
    if not reponse:
        return True
    if repond.est_fallback(reponse):
        return True
    try:
        import assistant_nl
        prefixes = tuple(p for p in (getattr(assistant_nl, "_PFX_INDECIDABLE", None),
                                     getattr(assistant_nl, "_PFX_SATURATION", None)) if p)
        if prefixes and reponse.startswith(prefixes):
            return True
    except Exception:
        pass
    return False


_RE_SOMMAIRE = re.compile(r"\b(sommaire|plan|table des mati[èe]res|de quoi (?:parle|traite)|r[ée]sum(?:e|é|er)|"
                          r"structure du (?:document|m[ée]moire|texte)|quelles? (?:sont les )?sections?)\b", re.I)


def _reponse_document(conv_id: str, question: str):
    """Réponse depuis le document attaché : opérations EXACTES sur les données structurées (Route 3), sommaire si
    demandé, sinon meilleur passage attribué. None si pas de document ou rien de pertinent (FAUX=0 : uniquement
    du contenu réel du document — valeur exacte localisée ou passage verbatim, jamais d'invention)."""
    donnees = _DONNEES.get(conv_id)
    if donnees is not None:
        try:
            import interroge_donnees
            r = interroge_donnees.repond(question, donnees)
            if r:
                return r
        except Exception:
            pass
    doc = _document_de(conv_id)
    if doc is None:
        return None
    titre = doc.titre or "le document"
    if _RE_SOMMAIRE.search(question or ""):
        som = doc.sommaire()
        if som:
            lignes = "\n".join("· %s (p. %d)" % (s["titre"], s["page"]) for s in som)
            return "Voici le plan que j'ai relevé dans « %s » :\n%s" % (titre, lignes)
        inf = doc.infos()
        return ("« %s » : %d page(s), %d passage(s) indexés. Pose-moi une question précise sur son contenu et "
                "je retrouve le passage exact." % (titre, inf["pages"], inf["passages"]))
    r = doc.repond(question)
    if not r:
        return None
    return "D'après « %s » (%s) :\n%s" % (titre, r["localisation"], r["reponse"])


def nouvelle_conversation(memoire, conv_id: str) -> dict:
    """Alloue une nouvelle conversation. NOTE D'HONNÊTETÉ : le stockage n'enregistre une conversation qu'au
    PREMIER message (un tour vide n'existe pas sur disque). On renvoie donc simplement l'id validé ; elle
    apparaîtra dans l'historique dès le premier message. `existe` indique si l'id est déjà utilisé."""
    cid = str(conv_id).strip()
    if not cid:
        return {"ok": False, "raison": "nom obligatoire"}
    # Si elle était ARCHIVÉE (cachée), la (re)créer/rouvrir la fait RÉAPPARAÎTRE : on l'utilise activement,
    # elle ne doit plus rester masquée de l'historique.
    arch = _lit_archive(memoire)
    if cid in arch:
        arch.discard(cid)
        _ecrit_archive(memoire, arch)
    return {"ok": True, "id": cid, "existe": cid in memoire.tours}


def oublie_conversation(memoire, conv_id: str) -> dict:
    """PURGE DÉFINITIVE (optionnelle) : supprime intégralement la conversation (mémoire + index + fichier disque)
    ET son entrée d'archive. Après ça, l'IA NE s'en souvient PLUS — à l'inverse d'archiver. À n'utiliser que si
    tu veux vraiment effacer pour de bon ; le geste courant de l'UI, lui, ARCHIVE (l'IA garde le souvenir)."""
    cid = str(conv_id)
    arch = _lit_archive(memoire)
    if cid in arch:
        arch.discard(cid)
        _ecrit_archive(memoire, arch)
    # Pendants RGPD EN-PROCESS : purger aussi l'état conversationnel volatil (clarification en attente,
    # sujet/question multi-tours) — sinon une question « oubliée » pouvait être REJOUÉE par un « oui » ultérieur.
    try:
        import assistant_nl
        assistant_nl.oublie_etat(cid)
    except Exception:
        pass
    repond._DERNIER_SUJET.pop(cid, None)
    repond._DERNIER_QUESTION.pop(cid, None)
    getattr(repond, "_QUIZ", {}).pop(cid, None)          # question de défi en attente : oubliée aussi
    _DOCS.pop(cid, None)                                 # document attaché : purgé aussi (RGPD en-process)
    _DONNEES.pop(cid, None)
    _FAITS_CONV.pop(cid, None)                           # faits personnels extraits : oubliés avec la conversation
    _SITUATIONS.pop(cid, None)                           # le fil : oublié aussi (RGPD en-process)
    return {"ok": memoire.oublie(cid)}


# ————————————————————————————————— TABLE DE ROUTES (évolutivité : 1 ligne par fonction future) —————————————————————————————————
# Chaque entrée : (méthode, chemin) -> handler(memoire, query_dict, body_dict) -> dict JSON.
# Ajouter « idées de projets » plus tard = ajouter une ligne ici + un panneau dans index.html. C'est tout.
def _resume_fichier(nom: str, res: dict) -> str:
    """Résumé FIDÈLE d'un fichier parsé (FAUX=0 : uniquement ce que le parseur a réellement lu, jamais inventé)."""
    if not isinstance(res, dict) or res.get("statut") != "verifie":
        return ("Je n'ai pas su lire « %s ». Je sais lire aujourd'hui : PDF (couche texte), json/geojson, "
                "csv/tsv, xml/rss/xsd, html, txt/md/log, ini/cfg/conf, sqlite/db, zip/tar/gz, svg. Les images "
                "et les PDF scannés (sans texte) ne sont pas encore pris en charge : il faudrait de l'OCR, "
                "prévu plus tard." % nom)
    typ, meta = res.get("type", "?"), res.get("meta") or {}
    contenu = res.get("contenu")
    # PDF / texte : on montre le TEXTE réellement extrait (pas un repr de dict). Un PDF sans couche texte
    # (scanné) est signalé HONNÊTEMENT via meta["note"] au lieu de faire croire à une lecture vide.
    if typ == "pdf" and isinstance(contenu, dict):
        pages = meta.get("pages", 0); avec = meta.get("pages_avec_texte", 0)
        if avec == 0:
            return ("J'ai ouvert « %s » : %d page(s), mais AUCUNE couche texte — c'est un PDF scanné (image). "
                    "Je ne peux pas encore le lire (OCR non disponible), et je n'invente rien." % (nom, pages))
        apercu = contenu.get("texte", "")
        tronque = len(apercu) > 800
        if tronque:
            apercu = apercu[:800].rsplit(" ", 1)[0] + " …"
        entete = "J'ai lu « %s » — %d page(s), %d avec du texte (%d caractères)" % (
            nom, pages, avec, meta.get("caracteres", 0))
        suite = "" if not tronque else ("\n\n(Aperçu du début. Pose-moi une question sur le contenu et je "
                                        "cherche le passage exact.)")
        return entete + " :\n" + apercu + suite
    if typ == "image" and isinstance(contenu, dict):
        txt = contenu.get("texte", "")
        if txt.strip():
            return "J'ai lu l'image « %s » et reconnu ce texte :\n%s" % (nom, txt)
        return ("J'ai ouvert l'image « %s » mais je n'y ai reconnu aucun texte net (mon OCR ne lit que du "
                "texte régulier à fort contraste, jamais deviné). Une photo ou une police manuscrite reste "
                "hors de portée pour l'instant." % nom)
    # CSV/TSV : résumé ACTIONNABLE (Route 3) — colonnes réelles + ce qu'on peut me demander dessus.
    if typ in ("csv", "tsv") and isinstance(contenu, list):
        try:
            import interroge_donnees
            tab = interroge_donnees.Tableau(contenu, titre=nom)
            if tab.n > 0:
                exemple = tab.entete[1] if len(tab.entete) > 1 else tab.entete[0]
                return ("J'ai lu « %s » : %d ligne(s) de données, colonnes : %s.\nTu peux m'interroger dessus, "
                        "par exemple : « quel est le max de %s ? », « moyenne de %s », « combien de lignes ? », "
                        "« quel est le %s de <une valeur de la 1ʳᵉ colonne> ? »." %
                        (nom, tab.n, ", ".join(tab.entete), exemple, exemple, exemple))
        except Exception:
            pass
    # JSON : résumé ACTIONNABLE — forme réelle du sommet + opérations disponibles.
    if typ == "json":
        try:
            import interroge_donnees
            arb = interroge_donnees.Arbre(contenu, titre=nom)
            cles, ou = arb._cles()
            forme = ("une liste de %d élément(s)" % len(contenu)) if isinstance(contenu, list) else \
                    ("un objet à %d clé(s)" % len(contenu)) if isinstance(contenu, dict) else "une valeur simple"
            det = (" Clés %s : %s." % (ou, ", ".join(map(str, cles[:15])))) if cles else ""
            return ("J'ai lu « %s » : %s.%s\nTu peux m'interroger dessus : « combien de <clé> ? », "
                    "« quelles sont les clés ? », « quel est le <clé> ? »." % (nom, forme, det))
        except Exception:
            pass
    apercu = str(contenu)
    if len(apercu) > 700:
        apercu = apercu[:700] + " …"
    entete = "J'ai lu « %s » (type %s)" % (nom, typ)
    meta_txt = str(meta)
    if meta_txt and meta_txt not in ("{}", ""):
        entete += " — " + meta_txt
    return entete + " :\n" + apercu


def importe_fichier(memoire, conv_id: str, nom: str, contenu_b64: str) -> dict:
    """Importe un fichier (base64) : le parse via ia.lit_fichier (json/csv/xml/sqlite/zip/ini…) et en donne un
    résumé fidèle. Souverain : le fichier est lu localement, jamais envoyé ailleurs ; effacé après lecture."""
    import base64, os, tempfile
    nom = (str(nom or "fichier").strip() or "fichier")
    try:
        data = base64.b64decode(contenu_b64 or "")
    except Exception:
        return {"ok": False, "raison": "contenu illisible", **lire_conversation(memoire, conv_id)}
    if len(data) > 40_000_000:      # 40 Mo : un mémoire de ~200 pages (texte + figures) tient largement
        return {"ok": False, "raison": "fichier trop volumineux (max 40 Mo)", **lire_conversation(memoire, conv_id)}
    ext = os.path.splitext(nom)[1]
    fd, chemin = tempfile.mkstemp(suffix=ext)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        import ia
        res = ia.lit_fichier(chemin)
    except Exception as e:
        res = {"statut": "erreur", "meta": str(e)}
    finally:
        try:
            os.remove(chemin)
        except OSError:
            pass
    arch = _lit_archive(memoire)                  # même invariant que ajoute_message : écrire dans une conv
    if conv_id in arch:                           # archivée la fait réapparaître (sinon l'import reste invisible)
        arch.discard(conv_id)
        _ecrit_archive(memoire, arch)
    memoire.ajoute(conv_id, "user", "\U0001F4CE " + nom)
    resume = _resume_fichier(nom, res)
    memoire.ajoute(conv_id, "ia", resume)
    _indexe_document(conv_id, nom, res)      # rend le document INTERROGEABLE (PDF/texte) pour les tours suivants
    return {"ok": True, "reponse": resume, **lire_conversation(memoire, conv_id)}


def _indexe_document(conv_id: str, nom: str, res: dict) -> None:
    """Si le fichier importé porte du TEXTE (PDF avec couche texte, ou fichier texte), on l'indexe en un
    `lecteur_document.Document` interrogeable, attaché à la conversation. Échec silencieux (best-effort)."""
    try:
        if not isinstance(res, dict) or res.get("statut") != "verifie":
            return
        typ, contenu = res.get("type"), res.get("contenu")
        # STRUCTURÉ (Route 3) : csv/tsv -> Tableau, json -> Arbre. Opérations exactes aux tours suivants.
        if typ in ("csv", "tsv") and isinstance(contenu, list):
            import interroge_donnees
            tab = interroge_donnees.Tableau(contenu, titre=nom)
            if tab.n > 0:
                _DONNEES[conv_id] = tab
            return
        if typ == "json":
            import interroge_donnees
            _DONNEES[conv_id] = interroge_donnees.Arbre(contenu, titre=nom)
            return
        import lecteur_document
        if typ == "pdf" and isinstance(contenu, dict) and contenu.get("pages"):
            doc = lecteur_document.Document(contenu["pages"], titre_document=nom)
        elif typ == "texte" and isinstance(contenu, str) and contenu.strip():
            doc = lecteur_document.Document(contenu, titre_document=nom)
        else:
            return
        if doc.n > 0:
            _DOCS[conv_id] = doc
    except Exception:
        pass


def _regle_langue(code) -> dict:
    """Fixe la langue de DISCUSSION (préférence globale du sélecteur d'interface). 'fr' = comportement natif."""
    code = (str(code or "fr")).strip().lower()
    try:
        import langue
        ok = code == "fr" or code in langue.LANGUES_SUPPORTEES
    except Exception:
        ok = code in ("fr", "en", "es", "de", "it", "pt")
    if not ok:
        return {"ok": False, "raison": "langue non supportée"}
    repond._PREF_LANGUE_GLOBAL[0] = None if code == "fr" else code
    return {"ok": True, "langue": code}


def _regle_web(actif) -> dict:
    """Interrupteur INTERNET de l'interface (recherche web ATTRIBUÉE) : ACTIF par défaut, coupé d'un clic.
    Process-global : IA_WEB est relu à CHAQUE question (repond + assistant_nl) -> effet immédiat. La base
    locale répond toujours ; couper internet ne coupe que la recherche de secours sur les sources externes."""
    os.environ["IA_WEB"] = "1" if actif else "0"
    return {"ok": True, "actif": os.environ.get("IA_WEB") == "1"}


ROUTES = {
    ("GET", "/api/status"):        lambda m, q, b: statut_chargement(),
    ("POST", "/api/installer-base"): lambda m, q, b: _installer_base(),
    ("POST", "/api/redemarrer"):   lambda m, q, b: _redemarrer(),
    ("POST", "/api/quitter"):      lambda m, q, b: _quitter(),
    ("GET", "/api/conversations"): lambda m, q, b: liste_conversations(m),
    ("GET", "/api/web"):           lambda m, q, b: {"ok": True, "actif": os.environ.get("IA_WEB") == "1"},
    ("POST", "/api/web"):          lambda m, q, b: _regle_web(bool(b.get("actif"))),
    ("GET", "/api/langue"):        lambda m, q, b: {"ok": True, "langue": repond._PREF_LANGUE_GLOBAL[0] or "fr"},
    ("POST", "/api/langue"):       lambda m, q, b: _regle_langue(b.get("langue")),
    ("GET", "/api/conversation"):  lambda m, q, b: lire_conversation(m, (q.get("id") or [""])[0]),
    ("POST", "/api/message"):      lambda m, q, b: ajoute_message(m, b.get("id", ""), b.get("texte", ""), pleine=_IA_PLEINE),
    ("POST", "/api/fichier"):      lambda m, q, b: importe_fichier(m, b.get("id", ""), b.get("nom", ""), b.get("contenu", "")),
    ("POST", "/api/nouvelle"):     lambda m, q, b: nouvelle_conversation(m, b.get("id", "")),
    ("POST", "/api/archive"):      lambda m, q, b: archive_conversation(m, b.get("id", "")),     # cacher (IA s'en souvient)
    ("GET", "/api/corbeille"):      lambda m, q, b: {"ok": True, "items": [i for i in liste_conversations(m, inclure_archivees=True)["items"] if i.get("archivee")]},
    ("POST", "/api/desarchive"):   lambda m, q, b: desarchive_conversation(m, b.get("id", "")),  # ré-afficher
    ("POST", "/api/oublie"):       lambda m, q, b: oublie_conversation(m, b.get("id", "")),       # purger pour de bon
    # MISES À JOUR : état (auto + disponibilité), réglage auto ON/OFF, vérif manuelle, application.
    ("GET", "/api/maj"):           lambda m, q, b: _maj_etat(),
    ("POST", "/api/maj/auto"):     lambda m, q, b: _maj_regle_auto(bool(b.get("actif"))),
    ("POST", "/api/maj/verifier"): lambda m, q, b: _maj_etat(force=True),
    ("POST", "/api/maj/appliquer"): lambda m, q, b: _maj_applique(b.get("url_exe")),
}


def _maj_etat(force: bool = False) -> dict:
    """État des mises à jour. On NE contacte le réseau QUE si Internet est activé (ou vérif manuelle forcée) —
    sinon on rend l'état local sans réseau (jamais de proposition sans réseau autorisé). FAUX=0 : proposition
    uniquement si une version réellement plus récente existe sur le dépôt officiel."""
    try:
        import maj
    except Exception as e:
        return {"ok": False, "message": "module de mise à jour indisponible : %r" % e}
    web_on = os.environ.get("IA_WEB") == "1"
    if not (web_on or force):
        loc = maj.version_locale()
        return {"ok": True, "auto": maj.auto_active(), "disponible": False, "reseau": False,
                "version_locale": loc.get("brut"), "version_distante": None, "url_exe": None}
    return maj.etat()


def _maj_regle_auto(actif: bool) -> dict:
    try:
        import maj
        return maj.regle_auto(actif)
    except Exception as e:
        return {"ok": False, "message": "%r" % e}


def _maj_applique(url_exe) -> dict:
    # GARDE INTERNET (trouvée au test LIVE 2026-07-06) : appliquer passait par version_distante() -> appel
    # réseau MÊME Internet coupé (contournait le toggle). Aucune requête sans consentement : refus actionnable.
    if os.environ.get("IA_WEB") != "1":
        return {"ok": False, "message": "Internet est coupé — réactive-le (bouton « 🌐 Internet ») pour "
                                        "vérifier et télécharger la mise à jour."}
    try:
        import maj
        r = maj.applique(url_exe)
        if r.get("ok") and r.get("redemarre"):
            # BUG RÉEL corrigé (test LIVE) : l'app promettait « va se fermer » mais ne se fermait JAMAIS —
            # l'updater attendait notre PID indéfiniment. On laisse la réponse HTTP partir (1,5 s) puis on
            # quitte VRAIMENT (os._exit : serveur threadé, et l'updater guette la fin du processus).
            import threading
            threading.Timer(1.5, lambda: os._exit(0)).start()
        return r
    except Exception as e:
        return {"ok": False, "message": "%r" % e}


class Handler(BaseHTTPRequestHandler):
    memoire = conversation.MEMOIRE        # le singleton « live » (dogfooding : l'IA et l'UI partagent ce stock)

    # — utilitaires de réponse —
    def _json(self, obj, code: int = 200) -> None:
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _page(self) -> None:
        try:
            with open(_HTML, "rb") as fh:
                data = fh.read()
        except FileNotFoundError:
            self.send_error(404, "index.html introuvable")
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _corps(self) -> dict:
        try:
            longueur = int(self.headers.get("Content-Length") or 0)
        except ValueError:                        # en-tête malformé -> corps vide (jamais de connexion coupée net)
            return {}
        if longueur <= 0:
            return {}
        brut = self.rfile.read(longueur)
        try:
            obj = json.loads(brut.decode("utf-8"))
            return obj if isinstance(obj, dict) else {}
        except (ValueError, UnicodeDecodeError):
            return {}

    # Origines LOCALES acceptées (page servie par CE serveur). Tout le reste est refusé (voir garde ci-dessous).
    _ORIGINE_LOCALE = re.compile(r"^https?://(?:127\.0\.0\.1|localhost|\[::1\])(?::\d+)?$", re.IGNORECASE)

    def _route(self, methode: str) -> None:
        # GARDE ANTI-CSRF / DNS-REBINDING : le serveur n'écoute que 127.0.0.1, mais une page web TIERCE ouverte
        # dans le navigateur peut quand même POSTer vers localhost (requête « simple », sans preflight CORS) ou
        # re-résoudre son domaine vers 127.0.0.1. On exige donc un Host LOCAL et, si le navigateur envoie une
        # Origin, une origin LOCALE -> aucune page externe ne peut actionner l'API (réactiver internet en douce,
        # purger une conversation, injecter des tours). curl/l'UI locale passent inchangés.
        hote = (self.headers.get("Host") or "").split(":")[0].strip("[]").lower()
        origine = self.headers.get("Origin")
        if hote not in ("127.0.0.1", "localhost", "::1") or (origine and not self._ORIGINE_LOCALE.match(origine)):
            self._json({"ok": False, "raison": "requête non locale refusée"}, code=403)
            return
        url = urlparse(self.path)
        if methode == "GET" and url.path in ("/", "/index.html"):
            self._page()
            return
        handler = ROUTES.get((methode, url.path))
        if handler is None:
            self._json({"ok": False, "raison": "route inconnue"}, code=404)
            return
        query = parse_qs(url.query)
        body = self._corps() if methode == "POST" else {}
        try:
            self._json(handler(self.memoire, query, body))
        except Exception as exc:                  # erreur honnête, jamais de 500 opaque pour le front
            self._json({"ok": False, "raison": f"{type(exc).__name__}: {exc}"}, code=400)

    def do_GET(self):
        self._route("GET")

    def do_POST(self):
        self._route("POST")

    def log_message(self, *_):                    # silence (pas de bruit dans le terminal partagé)
        pass


class _ServeurExclusif(ThreadingHTTPServer):
    """MONO-INSTANCE GARANTIE (vécu 2026-07-09 : DEUX Provara.exe écoutaient TOUS LES DEUX 127.0.0.1:8765 —
    netstat montrait un double LISTENING, requêtes routées au hasard). Cause : `allow_reuse_address` pose
    SO_REUSEADDR, et sous Windows deux sockets SO_REUSEADDR peuvent se lier au MÊME port. Ici : sous Windows,
    SO_EXCLUSIVEADDRUSE (le 2e bind échoue net) ; sur POSIX, SO_REUSEADDR reste (relance immédiate après
    TIME_WAIT, le double-bind n'y existe pas pour un port en écoute)."""
    allow_reuse_address = not hasattr(socket, "SO_EXCLUSIVEADDRUSE")

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def main():
    # Localhost STRICT : on lie 127.0.0.1, jamais 0.0.0.0 — les données ne sortent pas de la machine.
    port = int(os.environ.get("PORT", "8765"))
    try:
        serveur = _ServeurExclusif(("127.0.0.1", port), Handler)
    except OSError:
        # Une instance tourne DÉJÀ : on le DIT, on amène l'utilisateur à l'onglet existant, et on sort proprement
        # (jamais deux serveurs muets ; vécu : double-clic + relance = 2 instances silencieuses).
        print("Provara tourne déjà sur http://127.0.0.1:%d — j'ouvre l'onglet existant et je m'efface." % port,
              flush=True)
        if os.environ.get("VERAX_RELANCE_MAJ") != "1":
            try:
                import webbrowser
                webbrowser.open("http://127.0.0.1:%d" % port)
            except Exception:
                pass
        return
    n = len(Handler.memoire.conversations())
    mode = "IA PLEINE (connaissance vérifiée + mémoire)" if _IA_PLEINE else "léger (mémoire de dialogue seule)"
    print(f"Provara — assistant local souverain · http://127.0.0.1:{port}")
    print(f"  {n} conversation(s) sur le disque · mode : {mode}")
    if _IA_PLEINE:
        # Recherche web AUTONOME de l'assistant (assistant_nl -> veille.py, sources de confiance) : activée par
        # défaut en mode serveur PLEIN uniquement — gates et outils hors serveur restent sans réseau (opt-in).
        os.environ.setdefault("IA_WEB", "1")
        # Préchauffe le lecteur (~622 Mo, ~70 s) EN TÂCHE DE FOND : la page se sert tout de suite et, le temps
        # que tu écrives ta 1ʳᵉ question, la connaissance est déjà prête (sinon la 1ʳᵉ réponse attend la fin).
        import threading
        def _suit_progression(arret):
            """Poller (2026-07-12) : lit la progression PUBLIÉE par lecteur.PROGRES_CHARGE et l'expose en
            barre/% (web) + ligne CLI mise à jour en place. Sans ce retour, un préchargement muet de plusieurs
            minutes semble BLOQUÉ. Découplé : on lit un état, on n'appelle pas le lecteur (respect des couches ;
            le module apparaît dans sys.modules dès le début de son import, avant même la fin de son body)."""
            import sys as _sys, time as _t
            dernier = -1
            while not arret.is_set():
                m = _sys.modules.get("lecteur")
                p = getattr(m, "PROGRES_CHARGE", None) if m else None
                if p and p.get("total"):
                    pct = min(99, int(p["charges"] * 100 / p["total"]))   # 100 % réservé à « prêt »
                    if pct != dernier:
                        dernier = pct
                        _maj_statut(phase="chargement", pct=pct,
                                    detail="Chargement de la connaissance… %d/%d tables" % (p["charges"], p["total"]))
                        print("\r  … connaissance : %3d %% (%d/%d tables)   " % (pct, p["charges"], p["total"]),
                              end="", flush=True)
                    if p.get("fini"):
                        break
                _t.sleep(0.25)

        def _prechauffe():
            print("  … préchargement de la connaissance en cours (en fond)…", flush=True)
            _maj_statut(phase="chargement", detail="Chargement de la connaissance en mémoire…", pct=0)
            _arret = threading.Event()
            _poll = threading.Thread(target=_suit_progression, args=(_arret,), daemon=True)
            _poll.start()
            try:
                repond._charge_ia()
            except Exception as _e:
                print("  (préchargement : %s)" % _e, flush=True)
            _arret.set()
            _maj_statut(pret=True, phase="pret", detail="", pct=100)   # ferme la modale d'interface
            print("\r  ✓ connaissance prête.                              ", flush=True)
            # PRÉCHAUFFAGE DES PREUVES (après la connaissance, même thread de fond — un seul travail lourd à
            # la fois) : les preuves à sous-processus juge coûtent 10-60 s à froid sur le .exe ; passées ici,
            # « diagnostic » les sert du mémo daté au lieu de les compter « bloquée > 10s » (vécu 2026-07-09).
            try:
                import capacites as _CAPP
                _CAPP.chauffe_preuves()
                print("  ✓ preuves préchauffées (diagnostic complet immédiat).", flush=True)
            except Exception as _e:
                print("  (préchauffage preuves : %s)" % _e, flush=True)
        threading.Thread(target=_prechauffe, daemon=True).start()

        # VEILLE MISES À JOUR — ZÉRO ACTION UTILISATEUR (exigence Yohan : « beaucoup d'utilisateurs ne savent
        # pas se servir d'un PC, il faut qu'ils n'aient rien à faire ») :
        #   1) au DÉMARRAGE (20 s après le boot), si MAJ auto ON et version plus récente -> on APPLIQUE tout
        #      seul (l'app vient de s'ouvrir, le redémarrage est indolore). GARDE ANTI-BOUCLE : une cible déjà
        #      tentée récemment n'est pas re-tentée (un swap raté ne re-télécharge pas en boucle).
        #   2) ensuite, RE-VÉRIFICATION toutes les 15 min : une release publiée PENDANT que l'app tourne est
        #      détectée (bug réel : app lancée pendant le build CI -> aucune proposition jusqu'au prochain
        #      démarrage). Le front, qui repolle /api/maj, affiche alors la bannière sans aucun geste.
        def _veille_maj():
            import time as _t
            _t.sleep(20)
            premier = True
            while True:
                try:
                    if os.environ.get("IA_WEB") == "1":
                        import maj
                        e = maj.etat()
                        cible = e.get("version_distante") or ""
                        if (premier and e.get("disponible") and maj.auto_active()
                                and not maj.tentative_recente(cible)):
                            maj.note_tentative(cible)
                            # RETOUR VISUEL (2026-07-12) : le téléchargement du .exe est bloquant et était
                            # MUET côté UI — un « message de mise à jour » figé plusieurs minutes semble
                            # planté. On affiche une barre animée (indéterminée : le téléchargement ne
                            # rapporte pas de %) AVANT de lancer. `_maj_applique` ferme le process au succès ;
                            # sinon on efface le statut (l'app continue normalement).
                            _maj_statut(phase="maj_appli", maj_appli=True,
                                        detail="Mise à jour de Provara en cours… l'app va redémarrer seule.",
                                        pct=None)
                            r = _maj_applique(e.get("url_exe"))
                            if not (r.get("ok") and r.get("redemarre")):
                                _maj_statut(phase="", maj_appli=False, detail="")   # échec : on ne laisse pas la modale
                            if r.get("ok") and r.get("redemarre"):
                                return                          # l'app se ferme, l'updater prend le relais
                            # ⚠ ÉCHEC JAMAIS MUET (vécu build 77, 2026-07-09 : la 1ʳᵉ tentative auto vers 78 a
                            # échoué SANS TRACE ; la garde anti-boucle bloquait ensuite tout retry 6 h -> l'app
                            # restait en 77 sans que personne ne sache pourquoi). La cause va au log.
                            print("⚠ MAJ auto : échec de l'application -> %s"
                                  % (r.get("message") or r), flush=True)
                except Exception as _e:
                    print("⚠ MAJ auto : veille en erreur -> %r" % (_e,), flush=True)
                premier = False
                _t.sleep(900)
        threading.Thread(target=_veille_maj, daemon=True).start()
    else:
        _maj_statut(pret=True, phase="pret")                    # mode léger : rien à charger, pret tout de suite
    print(f"  Ctrl+C pour arrêter. (souverain : localhost uniquement)")
    try:
        serveur.serve_forever()
    except KeyboardInterrupt:
        print("\nArrêt.")
        serveur.server_close()


if __name__ == "__main__":
    main()
