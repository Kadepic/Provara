#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Provara — lanceur. Démarre l'interface web locale et ouvre le navigateur.

  • Sources :  python3 lance.py   (VERAX_FULL=1 pour installer la base complète)
  • .exe (Windows) : double-clic — installe la base complète au 1er lancement, puis instantané.

Localhost uniquement : les données ne quittent jamais la machine. Aucun GPU, aucune dépendance.
"""
import os
import sys

# MODE INTERPRÉTEUR JUGE (.exe) — AVANT TOUT AUTRE TRAVAIL : dans le bundle, sys.executable est Provara.exe ;
# le juge (juge.py/executeur.py) lance « Provara.exe --juge-exec candidat.py » pour exécuter un candidat dans
# un process isolé. Sans ce court-circuit, chaque candidat relançait l'APPLICATION ENTIÈRE (vécu .exe build 76,
# 2026-07-09 : preuves boucle/mesure bloquées, processus fantômes). Contrat du juge conservé : le fichier
# s'exécute tel quel, exception -> traceback + code retour ≠ 0, sentinelle imprimée sur stdout (pipé par juge).
if len(sys.argv) == 3 and sys.argv[1] == "--juge-exec":
    import runpy
    sys.argv = [sys.argv[2]]
    runpy.run_path(sys.argv[0], run_name="__main__")
    sys.exit(0)

import threading
import time
import webbrowser

if getattr(sys, "frozen", False):
    _ROOT = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(sys.executable)))
else:
    _ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _ROOT)
import verax_boot  # noqa: F401,E402  -- chemins + choix des données

# .exe (ou VERAX_FULL=1) : installe la base complète (72M faits) une fois, puis bascule dessus. Récupère AUSSI
# l'index .colf pré-construit -> démarrage ~30 Mo direct (sinon build à froid la 1ʳᵉ fois). `verax_boot` a déjà
# tourné (donc raté le cache tout juste téléchargé) : on fixe ici LECTEUR_CACHE_DIR + mode portable nous-mêmes.
# DÉMARRAGE INSTANTANÉ : Provara démarre TOUJOURS sur ce qui est déjà présent (échantillon embarqué au 1er
# lancement, ou base complète si elle a déjà été installée — verax_boot l'a déjà sélectionnée). Le
# téléchargement de la base complète (72M faits, ~1,2 Go + ~6 Go disque) est désormais OPTIONNEL et déclenché
# par l'UTILISATEUR depuis l'interface (bouton + modale d'info), jamais au lancement : on ne bloque JAMAIS
# l'ouverture. Routes côté serveur : /api/status · /api/installer-base · /api/redemarrer (interface/serveur.py).
pass

import glob as _glob
_dd = os.environ.get("LECTEUR_DATASETS_DIR", "")
_nrel = len(_glob.glob(os.path.join(_dd, "*.jsonl"))) if _dd and os.path.isdir(_dd) else 0
print("  donnees : %d relation(s) chargeables  [%s]" % (_nrel, _dd))
# INFO base (visible aussi pour ceux qui lancent depuis le terminal, pas seulement le .exe) :
try:
    import telecharge_donnees as _td
    if _td.base_complete_presente():
        print("  base    : COMPLÈTE (72 M de faits) active.")
    else:
        print("  base    : ÉCHANTILLON (Provara est utilisable tout de suite).")
        print("  >> Base complète (72 M de faits) OPTIONNELLE : ~6 Go d'espace disque, 15 à 20 minutes,")
        print("     UNIQUEMENT la première fois. Lancez-la depuis l'interface (bouton « Base complète »),")
        print("     ou en ligne de commande : VERAX_FULL=1 python3 lance.py")
except Exception:
    pass

# Ligne de commande : `VERAX_FULL=1` installe la base complète AVANT de démarrer (pour les usages scriptés/serveur,
# hors interface). L'utilisateur qui tape ça sait ce qu'il fait ; on l'avertit quand même clairement.
if os.environ.get("VERAX_FULL") == "1":
    try:
        import telecharge_donnees as _td2
        if not _td2.base_complete_presente():
            print("=" * 62)
            print("  VERAX_FULL=1 : installation de la base complète (72 M de faits).")
            print("  ~1,2 Go à télécharger + ~6 Go sur le disque. 15 À 20 MINUTES,")
            print("  une seule fois. Laissez tourner (progression ci-dessous)…")
            print("=" * 62)
            if _td2.assure_base_complete():
                os.environ["LECTEUR_DATASETS_DIR"] = _td2.dossier_donnees()
                _td2.assure_cache_complet()
                if _td2.cache_present() and "LECTEUR_CACHE_DIR" not in os.environ:
                    os.environ["LECTEUR_CACHE_DIR"] = _td2.dossier_cache()
                    os.environ.setdefault("LECTEUR_CACHE_PORTABLE", "1")
                print("  ✓ Base complète installée.")
    except Exception as _e:
        print("  (VERAX_FULL : installation impossible : %s — démarrage sur l'échantillon)" % _e)


def _build_id() -> str:
    """Commit du BUILD, tamponné dans VERSION_BUILD.txt (workflow CI / build_exe.bat) et embarqué dans le .exe.
    Affiché au démarrage : on sait toujours QUEL build on teste (un artifact périmé ne se distingue pas à l'œil).
    Hors .exe on répond « source » SANS lire le fichier : un reliquat de build local afficherait un tampon périmé."""
    if not getattr(sys, "frozen", False):
        return "source"
    try:
        with open(os.path.join(_ROOT, "VERSION_BUILD.txt"), "rb") as f:
            brut = f.read().decode("utf-8", "ignore")
        propre = "".join(c for c in brut if c.isalnum() or c in "._-")
        return propre[:12] or "?"
    except Exception:
        return "(non tamponné)"


print("  build   : %s" % _build_id())
os.environ.setdefault("IA_PLEINE", "1")
os.environ.setdefault("IA_WEB", "1")  # recherche structurée en secours (source fiable, attribuée)
_PORT = int(os.environ.get("PORT", "8765"))
_URL = "http://127.0.0.1:%d" % _PORT


def _ouvre_navigateur():
    # REDÉMARRAGE DE MISE À JOUR (vécu Yohan 2026-07-06 : « il m'ouvre un nouvel onglet, mais le précédent
    # n'est pas fermé ») : l'ancien onglet se RECHARGE tout seul (watchdog front) et un navigateur ne laisse
    # jamais le serveur fermer un onglet — donc on n'en OUVRE pas un deuxième. L'updater pose ce marqueur.
    if os.environ.get("VERAX_RELANCE_MAJ") == "1":
        return
    time.sleep(2.0)
    try:
        webbrowser.open(_URL)
    except Exception:
        pass


print("=" * 58)
print("  Provara — ouvre  %s" % _URL)
print("  localhost uniquement · aucun GPU · Ctrl+C pour arrêter")
print("=" * 58)
threading.Thread(target=_ouvre_navigateur, daemon=True).start()

sys.path.insert(0, os.path.join(_ROOT, "interface"))
import serveur  # noqa: E402  -- interface/serveur.py
serveur.main()
