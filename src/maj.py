# -*- coding: utf-8 -*-
"""MISES À JOUR du .exe Provara — vérification honnête contre les Releases GitHub, réglage persistant
(auto ON/OFF), et application (téléchargement + bascule du binaire + redémarrage).

Principe FAUX=0 : on ne PROPOSE une mise à jour QUE si une version RÉELLEMENT plus récente existe sur le dépôt
officiel (comparaison du tampon de build). Aucune requête réseau sans que l'utilisateur ait activé Internet.

Le tampon de build vit dans VERSION_BUILD.txt (le CI y écrit le commit + un numéro de build monotone) ; la Release
GitHub publie le même tampon dans un petit asset `version.txt`. On compare les deux : si le distant est différent
ET plus récent (numéro de build supérieur), une mise à jour est disponible.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request

_DEPOT = "Provara-IA/Provara"
_API_LATEST = "https://api.github.com/repos/%s/releases/latest" % _DEPOT
_ASSET_EXE = "Provara-windows.zip"          # asset contenant le nouveau .exe
_TIMEOUT = 15


def _dossier_config() -> str:
    base = os.environ.get("VERAX_HOME") or os.path.join(os.path.expanduser("~"), ".verax")
    try:
        os.makedirs(base, exist_ok=True)
    except OSError:
        pass
    return base


def _fichier_config() -> str:
    return os.path.join(_dossier_config(), "maj_config.json")


def _charge_config() -> dict:
    try:
        with open(_fichier_config(), encoding="utf-8") as f:
            d = json.load(f)
            return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _sauve_config(d: dict) -> None:
    try:
        with open(_fichier_config(), "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False)
    except OSError:
        pass


def auto_active() -> bool:
    """Les mises à jour automatiques sont-elles activées ? (défaut : True — l'utilisateur reste toujours maître,
    rien n'est appliqué sans sa confirmation à l'écran ; « auto » = on VÉRIFIE et on PROPOSE automatiquement.)"""
    return bool(_charge_config().get("auto", True))


def regle_auto(actif: bool) -> dict:
    d = _charge_config()
    d["auto"] = bool(actif)
    _sauve_config(d)
    return {"ok": True, "auto": bool(actif)}


def tentative_recente(cible: str, fenetre_s: int = 6 * 3600) -> bool:
    """L'auto-application a-t-elle DÉJÀ été tentée pour cette version cible récemment ? GARDE ANTI-BOUCLE :
    si un swap échoue (updater cassé, antivirus…), l'app redémarrerait sur l'ancienne version, re-détecterait
    la même MAJ et re-tenterait à l'infini (téléchargements en boucle). Une cible déjà tentée dans la fenêtre
    -> on ne RE-tente pas tout seul (la bannière manuelle reste disponible)."""
    import time
    d = _charge_config().get("tentative") or {}
    return d.get("cible") == cible and (time.time() - float(d.get("ts", 0))) < fenetre_s


def note_tentative(cible: str) -> None:
    import time
    d = _charge_config()
    d["tentative"] = {"cible": cible, "ts": time.time()}
    _sauve_config(d)


def _lire_tampon(texte: str) -> dict:
    """Extrait (build:int, commit:str) d'un tampon de build. Format tolérant : « <n> <commit> » ou juste un
    commit. Le NUMÉRO DE BUILD (entier monotone, tamponné par le CI) est ce qui décide « plus récent »."""
    txt = (texte or "").strip()
    build, commit = 0, ""
    if txt:
        parts = txt.replace("\n", " ").split()
        for p in parts:
            if p.isdigit() and build == 0:
                build = int(p)
            elif len(p) >= 6 and not commit:
                commit = "".join(c for c in p if c.isalnum())[:40]
    return {"build": build, "commit": commit, "brut": txt}


def version_locale() -> dict:
    """Tampon de build EMBARQUÉ dans ce .exe (VERSION_BUILD.txt). Hors .exe -> build 0 (source de dev)."""
    if not getattr(sys, "frozen", False):
        return {"build": 0, "commit": "source", "brut": "source"}
    racine = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(sys.executable)))
    try:
        with open(os.path.join(racine, "VERSION_BUILD.txt"), encoding="utf-8", errors="ignore") as f:
            return _lire_tampon(f.read())
    except OSError:
        return {"build": 0, "commit": "?", "brut": "?"}


def _transport(url: str, timeout: int = _TIMEOUT):
    """GET réseau (surchargeable pour les tests). Renvoie (code, bytes) ou lève."""
    req = urllib.request.Request(url, headers={"User-Agent": "Provara-MAJ", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:      # nosec — dépôt officiel en dur
        return r.status, r.read()


# point d'injection pour les tests (aucun réseau) : maj._TRANSPORT = lambda url, timeout=15: (200, b"...")
_TRANSPORT = None


def _get(url: str):
    fn = _TRANSPORT or _transport
    return fn(url, _TIMEOUT)


def version_distante() -> dict | None:
    """Tampon de build de la DERNIÈRE Release GitHub + URL de l'asset .exe. None si réseau indisponible/erreur
    (dégradation silencieuse : pas de réseau -> pas de proposition, jamais d'invention)."""
    try:
        code, corps = _get(_API_LATEST)
        if code != 200:
            return None
        rel = json.loads(corps.decode("utf-8"))
    except Exception:
        return None
    tag = rel.get("tag_name") or ""
    corps_notes = rel.get("body") or ""
    # tampon distant : d'abord un asset « version.txt » (le plus fiable), sinon le tag, sinon le corps.
    tampon = None
    url_exe = None       # .exe BRUT (préféré : aucun décompactage)
    url_zip = None       # paquet zip (repli)
    for a in rel.get("assets", []) or []:
        nom = a.get("name") or ""
        if nom == "version.txt":
            try:
                _c, _b = _get(a.get("browser_download_url"))
                tampon = _lire_tampon(_b.decode("utf-8", "ignore"))
            except Exception:
                tampon = None
        elif nom.lower() == "provara.exe":
            url_exe = a.get("browser_download_url")
        elif nom == _ASSET_EXE:
            url_zip = a.get("browser_download_url")
    if tampon is None:
        tampon = _lire_tampon(tag or corps_notes)
    tampon["url_exe"] = url_exe or url_zip
    tampon["est_zip"] = (url_exe is None and url_zip is not None)
    tampon["tag"] = tag
    return tampon


def etat() -> dict:
    """État complet pour l'interface : auto ON/OFF, disponibilité, tampons local/distant. Ne fait un appel réseau
    QUE si l'appelant l'a autorisé (le serveur ne l'appelle que quand Internet est activé)."""
    loc = version_locale()
    dist = version_distante()
    dispo = bool(dist and dist.get("build", 0) > loc.get("build", 0)
                 and dist.get("commit") and dist.get("commit") != loc.get("commit"))
    return {
        "ok": True,
        "auto": auto_active(),
        "disponible": dispo,
        "version_locale": loc.get("brut"),
        "version_distante": (dist or {}).get("brut"),
        "url_exe": (dist or {}).get("url_exe"),
        "reseau": dist is not None,
    }


def applique(url_exe: str | None = None) -> dict:
    """Télécharge le nouveau paquet et lance l'updater (bascule du binaire + redémarrage). Windows uniquement
    pour la bascule .exe. Renvoie {ok, message}. NE bloque PAS : l'updater tourne à part, l'app se ferme ensuite."""
    if not getattr(sys, "frozen", False):
        return {"ok": False, "message": "Mise à jour du binaire disponible seulement dans le .exe."}
    if not url_exe:
        d = version_distante()
        url_exe = d.get("url_exe") if d else None
    if not url_exe:
        return {"ok": False, "message": "Aucun paquet de mise à jour trouvé sur le dépôt."}
    import tempfile
    tmp = tempfile.gettempdir()
    nouveau = os.path.join(tmp, "Provara-nouveau.exe")
    try:
        _c, data = _get(url_exe)
    except Exception as e:
        return {"ok": False, "message": "Téléchargement échoué : %r" % e}
    est_zip = url_exe.lower().endswith(".zip")
    if est_zip:
        zip_path = os.path.join(tmp, "Provara-maj.zip")
        try:
            with open(zip_path, "wb") as f:
                f.write(data)
            import zipfile
            with zipfile.ZipFile(zip_path) as z:
                noms = [n for n in z.namelist() if n.lower().endswith("provara.exe")]
                if not noms:
                    return {"ok": False, "message": "Le paquet ne contient pas Provara.exe."}
                with z.open(noms[0]) as src, open(nouveau, "wb") as dst:
                    dst.write(src.read())
        except Exception as e:
            return {"ok": False, "message": "Extraction échouée : %r" % e}
    else:                                              # .exe BRUT : écriture directe, aucun décompactage
        try:
            with open(nouveau, "wb") as f:
                f.write(data)
        except Exception as e:
            return {"ok": False, "message": "Écriture échouée : %r" % e}
    return _lance_updater(nouveau)


def _lance_updater(nouveau_exe: str) -> dict:
    """Écrit un petit script Windows qui ATTEND la fermeture de l'app, remplace le binaire, puis relance."""
    cible = os.path.abspath(sys.executable)
    pid = os.getpid()
    import tempfile
    bat = os.path.join(tempfile.gettempdir(), "provara_updater.bat")
    # PIÈGES RÉELS corrigés (test LIVE 2026-07-06, build 38 -> 39) : (1) `timeout /t` EXIGE une console — lancé
    # sans fenêtre il échoue ; `ping -n` marche partout. (2) CREATE_NO_WINDOW et DETACHED_PROCESS sont
    # MUTUELLEMENT EXCLUSIFS (deux modes de console) — combinés, le comportement est indéfini et l'updater
    # mourait avec l'app. (3) CREATE_BREAKAWAY_FROM_JOB : si l'app vit dans un job Windows qui tue ses enfants,
    # l'updater doit s'en détacher pour survivre à la fermeture (repli sans le flag si le job l'interdit).
    contenu = (
        "@echo off\r\n"
        "echo Mise a jour de Provara en cours...\r\n"
        ":attente\r\n"
        'tasklist /FI "PID eq %d" 2>NUL | find "%d" >NUL\r\n' % (pid, pid) +
        "if not errorlevel 1 (\r\n"
        "  ping -n 2 127.0.0.1 >NUL\r\n"
        "  goto attente\r\n"
        ")\r\n"
        'move /Y "%s" "%s" >NUL\r\n' % (nouveau_exe, cible) +
        'start "" "%s"\r\n' % cible +
        # FILET ANTI-DLL (vécu : « Failed to load Python DLL …\_MEI…\python312.dll ») : au premier lancement
        # d'un binaire fraîchement téléchargé, l'antivirus peut verrouiller l'extraction PyInstaller et tuer
        # le démarrage. On vérifie après ~10 s que l'app tourne ; sinon on la relance UNE fois (le second
        # départ passe, le binaire ayant été scanné entre-temps).
        "ping -n 11 127.0.0.1 >NUL\r\n"
        'tasklist /FI "IMAGENAME eq Provara.exe" 2>NUL | find /I "Provara.exe" >NUL\r\n'
        "if errorlevel 1 (\r\n"
        "  ping -n 4 127.0.0.1 >NUL\r\n"
        '  start "" "%s"\r\n' % cible +
        ")\r\n"
        'del "%%~f0"\r\n'
    )
    try:
        with open(bat, "w", encoding="ascii", errors="ignore") as f:
            f.write(contenu)
        import subprocess
        no_win = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        breakaway = getattr(subprocess, "CREATE_BREAKAWAY_FROM_JOB", 0x01000000)
        try:
            subprocess.Popen(["cmd.exe", "/c", bat], creationflags=no_win | breakaway)
        except OSError:                                   # le job interdit le breakaway -> sans le flag
            subprocess.Popen(["cmd.exe", "/c", bat], creationflags=no_win)
    except Exception as e:
        return {"ok": False, "message": "Lancement de l'updater échoué : %r" % e}
    return {"ok": True, "message": "Mise à jour lancée. Provara va se fermer et redémarrer automatiquement.",
            "redemarre": True}
