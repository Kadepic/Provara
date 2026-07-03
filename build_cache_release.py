#!/usr/bin/env python3
"""Construit l'INDEX `.colf` PRÉ-CONSTRUIT à livrer dans une Release, à côté de la base complète (jsonl).

POURQUOI : sans index livré, le TOUT PREMIER lancement du produit construit le cache (pic RAM ~2,7 Go / ~6 min,
une seule fois) — problématique sur une petite machine. En livrant l'index, chaque lancement (dès le 1er) charge
en ~30 Mo / ~2 s (le corpus est mémoire-mappé, paginé à la demande). L'utilisateur extrait l'archive dans
`~/.verax/cache/` ; `verax_boot.py` la détecte et active le MODE CACHE PORTABLE (`LECTEUR_CACHE_PORTABLE=1`, qui
ignore le mtime des jsonl — changé par l'extraction — et se fie à leur TAILLE : intègre et sûr, FAUX=0 préservé).

À LANCER sur la machine qui possède la base COMPLÈTE, APRÈS toute mise à jour du code d'ingestion (l'index doit
refléter le code courant : normalisation `_norme_valeur`, etc. — sinon valeurs périmées).

Usage :
    export LECTEUR_DATASETS_DIR=/chemin/vers/datasets/lecteur      # base COMPLÈTE (jsonl)
    python3 build_cache_release.py [dossier_sortie]                # défaut : ./release_cache

Produit : <sortie>/cache/*.colf  +  <sortie>/verax_cache_v1.tar.gz (à joindre à la Release GitHub).
"""
import os
import subprocess
import sys
import tempfile
import time

_ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_ICI, "src"))


def main():
    datasets = os.environ.get("LECTEUR_DATASETS_DIR")
    if not datasets or not os.path.isdir(datasets):
        print("ERREUR : exporte LECTEUR_DATASETS_DIR vers la base COMPLÈTE (dossier des .jsonl).", file=sys.stderr)
        return 2
    sortie = sys.argv[1] if len(sys.argv) > 1 else os.path.join(_ICI, "release_cache")
    cache = os.path.join(sortie, "cache")
    os.makedirs(cache, exist_ok=True)
    # Build À NEUF depuis le code courant (aucun .bin/.colf réutilisé -> pas de valeur périmée).
    os.environ["LECTEUR_CACHE_DIR"] = cache
    os.environ["LECTEUR_MMAP"] = "1"
    os.environ.pop("LECTEUR_CACHE_PORTABLE", None)   # build local : invalidation stricte normale
    print(f"[1/3] Construction de l'index depuis {datasets}\n      -> {cache} (peut prendre plusieurs minutes)…")
    t0 = time.time()
    import lecteur  # noqa: l'import déclenche charge_dossier -> écrit les .colf VER 2
    n = len(lecteur.LECTEUR)
    print(f"      {n} faits, {len(lecteur.LECTEUR.tables)} tables, {time.time() - t0:.0f}s")
    colfs = [f for f in os.listdir(cache) if f.endswith(".colf")]
    print(f"[2/3] {len(colfs)} fichiers .colf écrits ({_taille(cache):.0f} Mo)")
    arch = os.path.join(sortie, "verax_cache_v1.tar.gz")
    print(f"[3/3] Archive -> {arch}")
    # tar déterministe (uniquement les .colf, à la racine de l'archive) via find -print0.
    with open(arch, "wb") as out:
        find = subprocess.Popen(["find", ".", "-maxdepth", "1", "-name", "*.colf", "-print0"],
                                cwd=cache, stdout=subprocess.PIPE)
        tar = subprocess.Popen(["tar", "--null", "-T", "-", "-cf", "-"], cwd=cache,
                               stdin=find.stdout, stdout=subprocess.PIPE)
        gz = subprocess.Popen(["gzip", "-1"], stdin=tar.stdout, stdout=out)
        gz.communicate()
    print(f"      OK ({os.path.getsize(arch) / (1024 * 1024):.0f} Mo)")
    print("\nÀ FAIRE : joindre verax_cache_v1.tar.gz à la Release ; l'utilisateur l'extrait dans ~/.verax/cache/ .")
    return 0


def _taille(d):
    return sum(os.path.getsize(os.path.join(d, f)) for f in os.listdir(d)) / (1024 * 1024)


if __name__ == "__main__":
    raise SystemExit(main())
