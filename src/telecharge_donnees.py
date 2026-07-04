# -*- coding: utf-8 -*-
"""Installe la base de connaissances COMPLÈTE (72M faits) depuis les Releases GitHub — pour que
l'IA embarquée (.exe) atteigne le niveau de la base complète, en un téléchargement unique. Récupère AUSSI
l'INDEX `.colf` pré-construit (démarrage ~30 Mo au lieu d'un build à froid la 1ʳᵉ fois).
stdlib pure (urllib + tarfile), souverain : rien d'autre que la donnée n'est récupéré."""
import os
import sys
import tarfile
import urllib.request

URL = os.environ.get(
    "VERAX_DONNEES_URL",
    "https://github.com/Verax-IA/Verax/releases/latest/download/datasets_complets.tar.gz")
URL_CACHE = os.environ.get(
    "VERAX_CACHE_URL",
    "https://github.com/Verax-IA/Verax/releases/latest/download/verax_cache_v1.tar.gz")


def dossier_donnees():
    """Dossier PERSISTANT des données (hors .exe, réinscriptible). Priorité : $VERAX_DATA_HOME, sinon ~/.verax."""
    base = os.environ.get("VERAX_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".verax")
    return os.path.join(base, "datasets", "lecteur")


def dossier_cache():
    """Dossier de l'index `.colf` pré-construit (frère de datasets/). Détecté par `verax_boot` -> mode portable."""
    base = os.environ.get("VERAX_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".verax")
    return os.path.join(base, "cache")


def base_complete_presente(seuil=200):
    d = dossier_donnees()
    try:
        return sum(1 for f in os.listdir(d) if f.endswith(".jsonl")) >= seuil
    except OSError:
        return False


def cache_present(seuil=200):
    d = dossier_cache()
    try:
        return sum(1 for f in os.listdir(d) if f.endswith(".colf")) >= seuil
    except OSError:
        return False


def _progres(lu, total):
    if total > 0:
        sys.stdout.write("\r  téléchargement… %3d%%  (%.0f Mo)"
                         % (min(100, lu * 100 // total), lu / 1048576))
        sys.stdout.flush()


def assure_base_complete(notifier=None):
    """Télécharge + installe la base complète si absente. Renvoie True si la base complète est prête.
    Échec réseau -> False (l'IA démarre alors sur l'échantillon embarqué : dégradation gracieuse).
    `notifier(phase=..., pct=...)` (optionnel) : rappelé pendant le téléchargement/décompression pour piloter
    une modale de progression côté interface. Best-effort, jamais bloquant."""
    def _note(**k):
        if notifier:
            try:
                notifier(**k)
            except Exception:
                pass
    if base_complete_presente():
        return True
    d = dossier_donnees()
    parent = os.path.dirname(d)
    os.makedirs(parent, exist_ok=True)
    arch = os.path.join(parent, "_datasets_complets.tar.gz")
    print("  Installation unique de la base complète (72M faits, ~560 Mo)…")
    _note(phase="telechargement", detail="Téléchargement de la base (72 M de faits)…", pct=0)
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
                if total:
                    _note(phase="telechargement", pct=round(lu * 100 / total))
        if total and lu != total:                 # INTÉGRITÉ : une archive tronquée ne doit JAMAIS être extraite
            raise IOError("téléchargement tronqué (%d octets sur %d)" % (lu, total))
        print("\n  extraction…")
        _note(phase="extraction", detail="Décompression de la base (~4 Go sur le disque)…", pct=None)
        with tarfile.open(arch) as t:
            try:
                t.extractall(parent, filter="data")   # Python 3.12+ : extraction sûre
            except TypeError:
                t.extractall(parent)
        os.remove(arch)
        print("  ✓ base complète installée (%s)." % d)
        return True
    except Exception as e:
        import urllib.error
        if isinstance(e, urllib.error.HTTPError) and e.code == 404:
            print("\n  (base complète pas encore publiée en ligne — VERAX démarre sur l'échantillon embarqué.\n"
                  "   Pour la base complète : place le dossier « lecteur » dans %s, ou attends sa publication.)"
                  % os.path.dirname(dossier_donnees()))
        else:
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


def assure_cache_complet(notifier=None):
    """Télécharge + extrait l'INDEX `.colf` pré-construit dans ~/.verax/cache si absent. Renvoie True si prêt.
    BEST-EFFORT : un échec (réseau, 404, archive absente d'une vieille Release) n'est PAS bloquant — VERAX
    reconstruira simplement l'index au 1er lancement (plus lent/lourd une seule fois). Intégrité : archive
    tronquée -> jamais extraite ; extraction partielle -> purgée (ne pas figer un cache incomplet).
    `notifier(phase=..., pct=...)` (optionnel) : progression pour la modale d'interface."""
    def _note(**k):
        if notifier:
            try:
                notifier(**k)
            except Exception:
                pass
    if cache_present():
        return True
    d = dossier_cache()
    os.makedirs(d, exist_ok=True)
    arch = os.path.join(os.path.dirname(d), "_verax_cache.tar.gz")
    print("  Installation de l'index pré-construit (démarrage ~30 Mo)…")
    _note(phase="index", detail="Téléchargement de l'index (démarrage rapide)…", pct=0)
    try:
        try:
            import https_confiance
            _ouvre = https_confiance.urlopen
        except Exception:
            _ouvre = urllib.request.urlopen
        req = urllib.request.Request(URL_CACHE, headers={"User-Agent": "VERAX/1.0 (cache)"})
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
                if total:
                    _note(phase="index", pct=round(lu * 100 / total))
        if total and lu != total:
            raise IOError("téléchargement tronqué (%d/%d)" % (lu, total))
        print("\n  extraction de l'index…")
        _note(phase="extraction_index", detail="Décompression de l'index…", pct=None)
        with tarfile.open(arch) as t:
            try:
                t.extractall(d, filter="data")
            except TypeError:
                t.extractall(d)
        os.remove(arch)
        print("  ✓ index installé (%s)." % d)
        return True
    except Exception as e:
        print("\n  (index pré-construit indisponible : %s — l'index sera reconstruit au 1er lancement)" % e)
        import shutil
        shutil.rmtree(d, ignore_errors=True)      # jamais un cache PARTIEL (sinon HIT sur des .colf manquants)
        try:
            os.remove(arch)
        except OSError:
            pass
        return False


if __name__ == "__main__":
    assure_base_complete()
    assure_cache_complet()
