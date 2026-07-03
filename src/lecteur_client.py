"""Client léger du daemon lecteur (OPTIM T9 — additif, stdlib pur, AUCUN `import lecteur`).

Permet au chemin interactif de répondre SANS charger la base (le daemon `lecteur_daemon.py` la détient).
`disponible()` -> True si le daemon écoute ; sinon l'appelant retombe sur son chemin habituel (opt-in,
jamais de régression). Import quasi-instantané, RAM ~0."""
from __future__ import annotations

import json
import os
import socket

SOCK = os.environ.get("LECTEUR_DAEMON_SOCK", "/dev/shm/lecteur_t9.sock")


def _appel(req: dict, timeout: float = 5.0) -> dict:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect(SOCK)
    try:
        s.sendall((json.dumps(req, ensure_ascii=False) + "\n").encode("utf-8"))
        buf = b""
        while b"\n" not in buf:
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
        return json.loads(buf.split(b"\n", 1)[0])
    finally:
        s.close()


def disponible() -> bool:
    try:
        return bool(_appel({"op": "ping"}, timeout=1.0).get("ok"))
    except OSError:
        return False


def cherche(relation: str, entite: str):
    """Valeur (str) ou None — miroir de `lecteur.cherche(...).valeur`."""
    return _appel({"op": "cherche", "rel": relation, "ent": entite}).get("valeur")


def repond_nl(question: str):
    """(statut, valeur|None) — miroir de `lecteur.repond_nl(...)`."""
    r = _appel({"op": "repond_nl", "q": question})
    return r.get("statut"), r.get("valeur")
