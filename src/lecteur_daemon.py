"""DAEMON RÉSIDENT du lecteur (OPTIM T9 — additif, stdlib pur).

Le chemin INTERACTIF (interface / T3 / tout usage Q-R en direct) paie aujourd'hui le COLD-LOAD du lecteur
(~2,7 Go / ~180 s sur le 9p) à CHAQUE démarrage de process, alors qu'il ne fait que QUELQUES lookups par
question. Ce daemon charge la base UNE seule fois et la sert sur une socket Unix (dans /dev/shm = RAM) :
les clients (cf. `lecteur_client.py`) répondent en ~ms sans rien charger.

NON lancé en permanence par défaut (il pèse ~2,7 Go résident — à n'allumer que quand l'interface tourne, pour
ne pas concurrencer les gates d'ingestion). Reload de la base sur SIGHUP (les datasets changent quand les lanes
ingèrent ; staleness acceptable pour le Q-R, rechargeable à la demande). FAUX=0 : sert EXACTEMENT ce que
`lecteur.cherche/repond_nl` renvoie (aucune logique de réponse ici)."""
from __future__ import annotations

import json
import os
import signal
import socketserver
import sys
import threading
import time

SOCK = os.environ.get("LECTEUR_DAEMON_SOCK", "/dev/shm/lecteur_t9.sock")

_LOCK = threading.RLock()          # sérialise reload vs requêtes (la base n'est pas thread-safe en reload)
_L = None                          # module lecteur, chargé paresseusement


def _charge():
    global _L
    import importlib
    if _L is None:
        import lecteur as L
        _L = L
    else:
        importlib.reload(_L)        # re-parse les datasets (SIGHUP) -> base fraîche
    return _L


def _traite(req: dict) -> dict:
    op = req.get("op")
    L = _L
    if op == "ping":
        return {"ok": True, "len": len(L.LECTEUR), "relations": len(L.LECTEUR.relations())}
    if op == "cherche":
        f = L.cherche(req["rel"], req["ent"])
        return {"valeur": None} if f is None else {"valeur": f.valeur, "source": f.source, "categorie": f.categorie}
    if op == "repond_nl":
        statut, f = L.repond_nl(req["q"])
        return {"statut": statut, "valeur": (f.valeur if f else None), "source": (f.source if f else None)}
    return {"erreur": "op inconnue: %r" % op}


class _Handler(socketserver.StreamRequestHandler):
    def handle(self):
        for ligne in self.rfile:                 # une requête JSON par ligne (connexion persistante OK)
            try:
                req = json.loads(ligne)
                with _LOCK:
                    rep = _traite(req)
            except Exception as e:               # jamais faire tomber le daemon sur une requête malformée
                rep = {"erreur": str(e)}
            self.wfile.write((json.dumps(rep, ensure_ascii=False) + "\n").encode("utf-8"))
            self.wfile.flush()


if hasattr(socketserver, "ThreadingUnixStreamServer"):
    class _Serveur(socketserver.ThreadingUnixStreamServer):
        daemon_threads = True
        allow_reuse_address = True
else:
    # Windows (.exe) : pas de socket Unix — vécu 2026-07-09 : la CLASSE au niveau module tuait l'IMPORT entier
    # (preuve « Daemon lecteur » rouge au diagnostic alors que `_traite`, pur, marche partout). Le daemon est
    # un confort de dev POSIX (cold-load partagé) ; sur cet hôte il se déclare indisponible, honnêtement.
    _Serveur = None


def main():
    if _Serveur is None:
        print("[daemon] indisponible sur cet hôte (pas de socket Unix) — le lecteur en-process reste la voie.",
              flush=True)
        return
    t0 = time.time()
    _charge()
    print("[daemon] base chargee len=%d relations=%d en %.1fs"
          % (len(_L.LECTEUR), len(_L.LECTEUR.relations()), time.time() - t0), flush=True)
    if os.path.exists(SOCK):
        os.unlink(SOCK)
    srv = _Serveur(SOCK, _Handler)

    def _reload(signum, frame):
        with _LOCK:
            t = time.time()
            _charge()
            print("[daemon] reload base len=%d en %.1fs" % (len(_L.LECTEUR), time.time() - t), flush=True)

    def _arret(signum, frame):
        raise KeyboardInterrupt                 # propage hors de serve_forever -> le `finally` nettoie la socket

    signal.signal(signal.SIGHUP, _reload)
    signal.signal(signal.SIGTERM, _arret)
    print("[daemon] ecoute sur %s (SIGHUP=reload, SIGTERM=arret)" % SOCK, flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.shutdown()
        if os.path.exists(SOCK):
            os.unlink(SOCK)
        print("[daemon] arrete", flush=True)


if __name__ == "__main__":
    main()
