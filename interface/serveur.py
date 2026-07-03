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
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

# Le module de stockage vit dans le dossier parent (harnais/). On l'ajoute au path SANS rien y écrire.
_ICI = os.path.dirname(os.path.abspath(__file__))
_HARNAIS = os.path.dirname(_ICI)
if _HARNAIS not in sys.path:
    sys.path.insert(0, _HARNAIS)

import conversation  # noqa: E402  (léger ; n'importe PAS `ia`)
import repond        # noqa: E402  (léger ; l'étage IA lourd est en import PARESSEUX, opt-in)

_HTML = os.path.join(_ICI, "index.html")

# IA pleine (étage 2 de repond.py) : ACTIVE PAR DÉFAUT (l'utilisateur veut tester l'IA réelle). Le lecteur
# (~622 Mo) est chargé PARESSEUSEMENT à la première question (pas au démarrage). Pour forcer le mode léger
# (mémoire de dialogue seule, sans charger le lecteur), lancer avec IA_LEGER=1.
# ⚠️ Cohabitation : éviter de lancer en mode plein PENDANT qu'un autre process lourd charge le lecteur (OOM WSL).
_IA_PLEINE = os.environ.get("IA_LEGER") != "1"


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
    seq = memoire.ajoute(conv_id, "user", texte, scope=scope)        # STOCKE D'ABORD : jamais perdu, jamais bloqué
    # La réponse filtre déjà le message courant (texte != courant) -> pas d'auto-citation malgré l'indexation.
    reponse = repond.repond(memoire, conv_id, texte, pleine=pleine)
    if reponse:
        memoire.ajoute(conv_id, "ia", reponse, scope=scope)          # réponse sound, durable, verbatim
    return {"ok": seq >= 0, "seq": seq, "reponse": reponse, **lire_conversation(memoire, conv_id)}


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
    return {"ok": memoire.oublie(cid)}


# ————————————————————————————————— TABLE DE ROUTES (évolutivité : 1 ligne par fonction future) —————————————————————————————————
# Chaque entrée : (méthode, chemin) -> handler(memoire, query_dict, body_dict) -> dict JSON.
# Ajouter « idées de projets » plus tard = ajouter une ligne ici + un panneau dans index.html. C'est tout.
ROUTES = {
    ("GET", "/api/conversations"): lambda m, q, b: liste_conversations(m),
    ("GET", "/api/conversation"):  lambda m, q, b: lire_conversation(m, (q.get("id") or [""])[0]),
    ("POST", "/api/message"):      lambda m, q, b: ajoute_message(m, b.get("id", ""), b.get("texte", ""), pleine=_IA_PLEINE),
    ("POST", "/api/nouvelle"):     lambda m, q, b: nouvelle_conversation(m, b.get("id", "")),
    ("POST", "/api/archive"):      lambda m, q, b: archive_conversation(m, b.get("id", "")),     # cacher (IA s'en souvient)
    ("POST", "/api/desarchive"):   lambda m, q, b: desarchive_conversation(m, b.get("id", "")),  # ré-afficher
    ("POST", "/api/oublie"):       lambda m, q, b: oublie_conversation(m, b.get("id", "")),       # purger pour de bon
}


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
        longueur = int(self.headers.get("Content-Length") or 0)
        if longueur <= 0:
            return {}
        brut = self.rfile.read(longueur)
        try:
            obj = json.loads(brut.decode("utf-8"))
            return obj if isinstance(obj, dict) else {}
        except (ValueError, UnicodeDecodeError):
            return {}

    def _route(self, methode: str) -> None:
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


def main():
    # Localhost STRICT : on lie 127.0.0.1, jamais 0.0.0.0 — les données ne sortent pas de la machine.
    port = int(os.environ.get("PORT", "8765"))
    serveur = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    n = len(Handler.memoire.conversations())
    mode = "IA PLEINE (connaissance vérifiée + mémoire)" if _IA_PLEINE else "léger (mémoire de dialogue seule)"
    print(f"Interface mémoire de conversation — http://127.0.0.1:{port}")
    print(f"  {n} conversation(s) sur le disque · mode : {mode}")
    if _IA_PLEINE:
        # Recherche web AUTONOME de l'assistant (assistant_nl -> veille.py, sources de confiance) : activée par
        # défaut en mode serveur PLEIN uniquement — gates et outils hors serveur restent sans réseau (opt-in).
        os.environ.setdefault("IA_WEB", "1")
        # Préchauffe le lecteur (~622 Mo, ~70 s) EN TÂCHE DE FOND : la page se sert tout de suite et, le temps
        # que tu écrives ta 1ʳᵉ question, la connaissance est déjà prête (sinon la 1ʳᵉ réponse attend la fin).
        import threading
        def _prechauffe():
            print("  … préchargement de la connaissance en cours (~1 min, en fond)…", flush=True)
            repond._charge_ia()
            print("  ✓ connaissance prête.", flush=True)
        threading.Thread(target=_prechauffe, daemon=True).start()
    print(f"  Ctrl+C pour arrêter. (souverain : localhost uniquement)")
    try:
        serveur.serve_forever()
    except KeyboardInterrupt:
        print("\nArrêt.")
        serveur.server_close()


if __name__ == "__main__":
    main()
