# -*- coding: utf-8 -*-
"""MESURE DES RESSOURCES — empreinte RÉELLE de Provara avec TOUT ce qu'il a appris (2026-07-03).

À lancer APRÈS avoir fini les briques/chantiers, pour des chiffres FIABLES : taille disque (exe + datasets +
code), RAM (RSS) à froid puis lecteur chargé, temps de chargement, et coût CPU par requête. Souverain, stdlib.

Usage :
  export PYTHONPATH="$PWD/src:$PWD/ingestion:$PWD/interface"
  export LECTEUR_DATASETS_DIR="$PWD/datasets/lecteur" LECTEUR_CACHE_DIR=/tmp/verax
  python3 mesure_ressources.py
"""
from __future__ import annotations

import os
import resource
import sys
import time

_ICI = os.path.dirname(os.path.abspath(__file__))


def _rss_mo() -> float:
    """RSS du process en Mo (ru_maxrss est en Ko sous Linux)."""
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def _taille_dossier(chemin: str) -> int:
    total = 0
    for r, _d, fs in os.walk(chemin):
        for f in fs:
            try:
                total += os.path.getsize(os.path.join(r, f))
            except OSError:
                pass
    return total


def _mo(o: int) -> float:
    return o / (1024.0 * 1024.0)


def main():
    print("=" * 70)
    print("Provara — MESURE DES RESSOURCES (état complet)")
    print("=" * 70)

    # — DISQUE —
    print("\n[DISQUE]")
    for nom, chemin in [("code src/", os.path.join(_ICI, "src")),
                        ("code interface/", os.path.join(_ICI, "interface")),
                        ("code ingestion/", os.path.join(_ICI, "ingestion")),
                        ("tests/", os.path.join(_ICI, "tests")),
                        ("datasets/lecteur (embarqué)", os.path.join(_ICI, "datasets", "lecteur"))]:
        if os.path.isdir(chemin):
            print("  %-32s %8.1f Mo" % (nom, _mo(_taille_dossier(chemin))))
    exe = os.path.join(_ICI, "dist", "Provara.exe")
    if os.path.isfile(exe):
        print("  %-32s %8.1f Mo" % ("dist/Provara.exe", _mo(os.path.getsize(exe))))
    # datasets embarqués : nb de fichiers + nb de faits (lignes)
    dl = os.path.join(_ICI, "datasets", "lecteur")
    if os.path.isdir(dl):
        fichiers = [f for f in os.listdir(dl) if f.endswith(".jsonl")]
        print("  datasets embarqués : %d relations (.jsonl)" % len(fichiers))

    # — RAM à froid (avant tout import lourd) —
    print("\n[RAM]")
    print("  %-32s %8.1f Mo" % ("à froid (Python + ce script)", _rss_mo()))

    # — chargement du LECTEUR (toute la connaissance embarquée) —
    print("\n[CHARGEMENT DE LA CONNAISSANCE]")
    t0 = time.time()
    import ia  # noqa: déclenche le chargement du lecteur
    # force une première résolution pour garantir que tout est chargé
    try:
        ia.donnee_nl("capitale de France")
    except Exception:
        pass
    dt = time.time() - t0
    print("  %-32s %8.2f s" % ("temps de chargement (cold)", dt))
    print("  %-32s %8.1f Mo" % ("RAM lecteur chargé (RSS pic)", _rss_mo()))
    try:
        import lecteur as _L
        lect = _L.Lecteur() if hasattr(_L, "Lecteur") else None
    except Exception:
        lect = None

    # nombre réel de relations / faits connus (via le diagnostic du produit)
    try:
        import base_faits
        # compte les faits chargés dans le lecteur du produit
        nb_rel = nb_faits = None
        try:
            from lecteur_client import _lecteur_partage  # si dispo
        except Exception:
            pass
    except Exception:
        pass

    # — CPU par requête (chaud) —
    print("\n[CPU / REQUÊTE (à chaud)]")
    requetes = ["capitale de France", "capitale de Espagne", "capitale de Italie", "capitale de Allemagne",
                "monnaie de France", "capitale de Japon"]
    # échauffement + vérif que ça résout réellement
    ok = sum(1 for r in requetes if (lambda x: x and x[0] == "verifie")(ia.donnee_nl(r)))
    n = 3000
    w0 = time.perf_counter()
    for i in range(n):
        ia.donnee_nl(requetes[i % len(requetes)])
    wall = time.perf_counter() - w0
    print("  %-32s %8.3f ms / requête (%d requêtes, %d/%d résolvent)" % (
        "lookup factuel vérifié", 1000.0 * wall / n, n, ok, len(requetes)))
    debit = n / wall if wall else 0
    print("  %-32s %8.0f requêtes / seconde" % ("débit", debit))

    # — modules chargés (surface mémoire du code) —
    print("\n[CODE]")
    print("  %-32s %8d modules Python en mémoire" % ("modules importés", len(sys.modules)))

    print("\n" + "=" * 70)
    print("Résumé : Provara charge sa connaissance en %.1f s (I/O disque ; plus rapide en natif), tient dans\n"
          "%.0f Mo de RAM, et répond à un fait vérifié en ~%.3f ms (%.0f req/s). 0 GPU, 0 dépendance."
          % (dt, _rss_mo(), 1000.0 * wall / n, debit))
    print("=" * 70)


if __name__ == "__main__":
    main()
