# -*- coding: utf-8 -*-
"""Installe la base de connaissances COMPLÈTE (73M faits) depuis les Releases GitHub — pour que
l'IA embarquée (.exe) atteigne le niveau de la base complète, en un téléchargement unique.
stdlib pure (urllib + tarfile), souverain : rien d'autre que la donnée n'est récupéré."""
import os
import sys
import tarfile
import urllib.request

URL = os.environ.get(
    "VERAX_DONNEES_URL",
    "https://github.com/Verax-IA/Verax/releases/latest/download/datasets_complets.tar.gz")


def dossier_donnees():
    """Dossier PERSISTANT des données (hors .exe, réinscriptible). Priorité : $VERAX_DATA_HOME, sinon ~/.verax."""
    base = os.environ.get("VERAX_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".verax")
    return os.path.join(base, "datasets", "lecteur")


def base_complete_presente(seuil=200):
    d = dossier_donnees()
    try:
        return sum(1 for f in os.listdir(d) if f.endswith(".jsonl")) >= seuil
    except OSError:
        return False


def _progres(lu, total):
    if total > 0:
        sys.stdout.write("\r  téléchargement de la base complète… %3d%%  (%.0f Mo)"
                         % (min(100, lu * 100 // total), lu / 1048576))
        sys.stdout.flush()


def assure_base_complete():
    """Télécharge + installe la base complète si absente. Renvoie True si la base complète est prête.
    Échec réseau -> False (l'IA démarre alors sur l'échantillon embarqué : dégradation gracieuse)."""
    if base_complete_presente():
        return True
    d = dossier_donnees()
    parent = os.path.dirname(d)
    os.makedirs(parent, exist_ok=True)
    arch = os.path.join(parent, "_datasets_complets.tar.gz")
    print("  Installation unique de la base complète (73M faits, ~750 Mo)…")
    try:
        try:
            import https_confiance            # repli épinglé (magasin Windows parfois pollué -> faux « expired »)
            _ouvre = https_confiance.urlopen
        except Exception:
            _ouvre = urllib.request.urlopen   # layout minimal sans src/ -> comportement d'avant
        req = urllib.request.Request(URL, headers={"User-Agent": "VERAX/1.0 (base complete)"})
        with _ouvre(req, timeout=60) as r, open(arch, "wb") as fh:
            total = int(r.headers.get("Content-Length") or 0)
            lu = 0
            while True:
                bloc = r.read(1 << 20)
                if not bloc:
                    break
                fh.write(bloc)
                lu += len(bloc)
                _progres(lu, total)
        if total and lu != total:                 # INTÉGRITÉ : une archive tronquée ne doit JAMAIS être extraite
            raise IOError("téléchargement tronqué (%d octets sur %d)" % (lu, total))
        print("\n  extraction…")
        with tarfile.open(arch) as t:
            try:
                t.extractall(parent, filter="data")   # Python 3.12+ : extraction sûre
            except TypeError:
                t.extractall(parent)
        os.remove(arch)
        print("  ✓ base complète installée (%s)." % d)
        return True
    except Exception as e:
        print("\n  (base complète indisponible : %s — démarrage sur l'échantillon)" % e)
        # NETTOYAGE : ne JAMAIS laisser une extraction PARTIELLE se faire passer pour la base complète —
        # base_complete_presente() compte les .jsonl, ≥200 fichiers partiels la figeraient « complète » à vie
        # (et une relation coupée sur une frontière de ligne serait chargée comme si elle était entière).
        # Sûr : on n'arrive ici que si la base n'était PAS complète à l'entrée (early-return sinon).
        import shutil
        shutil.rmtree(d, ignore_errors=True)
        try:
            os.remove(arch)
        except OSError:
            pass
        return False


if __name__ == "__main__":
    assure_base_complete()
