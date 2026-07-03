#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VALIDE lecteur_daemon + lecteur_client — le CHEMIN RAPIDE interactif (OPTIM), FAUX=0, sans régression.

Contrat jugé :
  • daemon lancé  -> `lecteur_client.disponible()` True ; `cherche`/`repond_nl` renvoient EXACTEMENT ce que
    `lecteur.cherche`/`lecteur.repond_nl` renvoient (parité stricte — le daemon n'a AUCUNE logique de réponse) ;
  • entité inconnue -> None (jamais inventé) ;
  • le chemin rapide de l'interface (`repond._connaissance_rapide_daemon`) rend la même valeur que le chemin lourd ;
  • daemon ARRÊTÉ -> `disponible()` False -> l'appelant retombe sur son chemin habituel (opt-in, zéro régression).

Léger & portable : fixture = UNE petite relation existante (capitale) copiée dans un dossier temporaire ;
socket Unix temporaire (pas /dev/shm) ; le daemon charge cette fixture seule (pas les 73 M faits).
"""
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time

_ICI = os.path.dirname(os.path.abspath(__file__)) or "."
sys.path.insert(0, _ICI)

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print("  FAIL: " + l)


# ── fixture : un dossier de datasets minimal (une relation existante suffit) ──
_TMP = tempfile.mkdtemp(prefix="verax_daemon_")
_DS = os.path.join(_TMP, "lecteur")
os.makedirs(_DS)
_SRC = os.path.join(os.environ.get("LECTEUR_DATASETS_DIR") or os.path.join(_ICI, "datasets", "lecteur"), "capitale.jsonl")
if not os.path.exists(_SRC):
    print("=== valide_lecteur_client : 0/0 (fixture capitale.jsonl absente — SKIP) ===")
    shutil.rmtree(_TMP, ignore_errors=True)
    sys.exit(0)
shutil.copy(_SRC, os.path.join(_DS, "capitale.jsonl"))

_SOCK = os.path.join(_TMP, "d.sock")
os.environ["LECTEUR_DAEMON_SOCK"] = _SOCK
os.environ["LECTEUR_DATASETS_DIR"] = _DS
os.environ["LECTEUR_CACHE_DIR"] = os.path.join(_TMP, "cache")

import lecteur_client

# état initial : daemon PAS lancé -> indisponible, fallback propre
check(lecteur_client.disponible() is False, "daemon absent -> disponible() False (fallback, pas d'erreur)")

# vérité de référence : le lecteur chargé DIRECTEMENT sur la même fixture
import lecteur as _L
ref_japon = _L.cherche("capitale", "Japon")
ref_val = ref_japon.valeur if ref_japon else None
check(ref_val is not None, "référence : lecteur.cherche(capitale, Japon) trouve une valeur")

daemon = None
try:
    env = dict(os.environ)
    daemon = subprocess.Popen([sys.executable, os.path.join(os.environ.get("VERAX_ROOT") or _ICI, "src", "lecteur_daemon.py")],
                              env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=_ICI)
    # attendre que le daemon écoute (fixture = charge quasi-instantanée)
    t0 = time.time()
    up = False
    while time.time() - t0 < 30:
        if lecteur_client.disponible():
            up = True
            break
        time.sleep(0.2)
    check(up, "daemon lancé -> disponible() True en < 30 s")

    if up:
        # PARITÉ stricte : le client rend EXACTEMENT lecteur.cherche(...).valeur
        check(lecteur_client.cherche("capitale", "Japon") == ref_val,
              "parité cherche : client == lecteur.cherche(...).valeur (Tokyo)")
        ref_fr = _L.cherche("capitale", "France")
        check(lecteur_client.cherche("capitale", "France") == (ref_fr.valeur if ref_fr else None),
              "parité cherche : France (2e ancre)")
        # entité inconnue -> None (jamais inventé)
        check(lecteur_client.cherche("capitale", "Wakanda") is None,
              "inconnu -> None (FAUX=0, rien inventé)")
        # parité repond_nl (statut, valeur)
        s_ref, f_ref = _L.repond_nl("Quelle est la capitale du Japon ?")
        s_cli, v_cli = lecteur_client.repond_nl("Quelle est la capitale du Japon ?")
        check(s_cli == s_ref and v_cli == (f_ref.valeur if f_ref else None),
              "parité repond_nl : (statut, valeur) identiques au lecteur")

        # CHEMIN RAPIDE de l'interface : même valeur que le chemin lourd, sans cold-load
        sys.path.insert(0, os.path.join(os.environ.get("VERAX_ROOT") or _ICI, "interface"))
        import importlib.util
        spec = importlib.util.spec_from_file_location("repond_test", os.path.join(os.environ.get("VERAX_ROOT") or _ICI, "interface", "repond.py"))
        R = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(R)
        rapide = R._connaissance_rapide_daemon("Quelle est la capitale du Japon ?")
        check(rapide == ref_val, "interface chemin rapide -> même valeur que le lecteur (Tokyo)")
        check(R._connaissance_rapide_daemon("Quelle est la capitale du Wakanda ?") is None,
              "interface chemin rapide : inconnu -> None (retombe sur le chemin lourd)")
finally:
    if daemon is not None:
        daemon.send_signal(signal.SIGTERM)
        try:
            daemon.wait(timeout=10)
        except subprocess.TimeoutExpired:
            daemon.kill()

# daemon arrêté -> indisponible de nouveau (fallback restauré)
time.sleep(0.3)
check(lecteur_client.disponible() is False, "daemon arrêté -> disponible() False (régression impossible)")

shutil.rmtree(_TMP, ignore_errors=True)
print(f"\n=== valide_lecteur_client : {ok}/{ok + ko} ===")
sys.exit(0 if ko == 0 else 1)
