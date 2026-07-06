# -*- coding: utf-8 -*-
"""Gate MISES À JOUR (src/maj.py) : vérifie la logique de version SANS réseau (transport injecté) — parsing du
tampon, réglage auto persistant, détection « plus récent » (build monotone), FAUX=0 (jamais de proposition sans
version réellement supérieure ni sans réseau)."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["VERAX_HOME"] = tempfile.mkdtemp()
import maj  # noqa: E402

_ok = [0]
_ko = [0]


def check(cond, label):
    if cond:
        _ok[0] += 1
    else:
        _ko[0] += 1
        print("  FAIL:", label)


# — parsing du tampon —
check(maj._lire_tampon("42 abc123def")["build"] == 42, "tampon : build extrait")
check(maj._lire_tampon("42 abc123def")["commit"] == "abc123def", "tampon : commit extrait")
check(maj._lire_tampon("")["build"] == 0, "tampon vide -> build 0")

# — réglage auto persistant —
check(maj.auto_active() is True, "auto activé par défaut")
maj.regle_auto(False)
check(maj.auto_active() is False, "auto désactivé persiste")
maj.regle_auto(True)
check(maj.auto_active() is True, "auto réactivé persiste")


def _transport(build_distant):
    def t(url, timeout=15):
        if "releases/latest" in url:
            return 200, json.dumps({"tag_name": "latest", "assets": [
                {"name": "version.txt", "browser_download_url": "http://x/version.txt"},
                {"name": "Provara.exe", "browser_download_url": "http://x/Provara.exe"}]}).encode()
        if "version.txt" in url:
            return 200, ("%d cafe1234" % build_distant).encode()
        return 404, b""
    return t


# — détection « plus récent » —
maj._TRANSPORT = _transport(99)
d = maj.version_distante()
check(d["build"] == 99 and d["url_exe"].endswith("Provara.exe"), "version distante lue (build + url .exe brut)")
check(d["est_zip"] is False, "asset .exe brut préféré (pas le zip)")

# hors .exe (source), version_locale build 0 -> distant 99 -> disponible
e = maj.etat()
check(e["disponible"] is True, "MAJ disponible quand distant > local")
check(e["version_distante"] == "99 cafe1234", "état : version distante rapportée")

# distant PLUS ANCIEN ou ÉGAL -> jamais de fausse proposition (FAUX=0)
maj._TRANSPORT = _transport(0)
check(maj.etat()["disponible"] is False, "FAUX=0 : pas de MAJ si distant <= local")

# réseau indisponible -> pas de proposition (dégradation silencieuse)
def _ko_transport(url, timeout=15):
    raise OSError("pas de réseau")
maj._TRANSPORT = _ko_transport
check(maj.version_distante() is None, "réseau KO -> version distante None")
check(maj.etat()["disponible"] is False, "réseau KO -> aucune MAJ proposée")

# UPDATER (bugs trouvés au test LIVE build 38->39, 2026-07-06) : le .bat doit marcher SANS console
# (« timeout /t » exige une console -> « ping -n »), se détacher d'un éventuel job Windows, et l'app doit
# VRAIMENT se fermer après « appliquer » (garde côté serveur). Vérifié sur les SOURCES, sans lancer d'updater.
import inspect
_src = inspect.getsource(maj._lance_updater)
check("ping -n" in _src, "updater : attente par ping (marche sans console)")
check("timeout /t 1" not in _src, "updater : plus de la commande « timeout /t 1 » (exige une console)")
check("CREATE_BREAKAWAY_FROM_JOB" in _src, "updater : breakaway du job (survit à la fermeture de l'app)")
check('getattr(subprocess, "DETACHED_PROCESS"' not in _src,
      "updater : plus de DETACHED_PROCESS (exclusif avec CREATE_NO_WINDOW)")
with open(os.path.join(os.path.dirname(__file__), "..", "interface", "serveur.py"), encoding="utf-8") as _f:
    _src_srv = _f.read()
check("os._exit(0)" in _src_srv, "serveur : l'app se ferme réellement après « appliquer »")
check("Internet est coupé" in _src_srv, "serveur : « appliquer » refusé si Internet OFF (pas d'appel caché)")

# ZÉRO ACTION UTILISATEUR (exigence 2026-07-06) : auto-application au démarrage + garde anti-boucle + veille.
check(maj.tentative_recente("40 abc") is False, "anti-boucle : cible jamais tentée -> False")
maj.note_tentative("40 abc")
check(maj.tentative_recente("40 abc") is True, "anti-boucle : cible tentée récemment -> True (pas de re-boucle)")
check(maj.tentative_recente("41 def") is False, "anti-boucle : NOUVELLE cible -> False (la MAJ suivante passe)")
check("_veille_maj" in _src_srv, "serveur : veille MAJ périodique câblée")
check("maj.tentative_recente" in _src_srv, "serveur : auto-apply gardé par l'anti-boucle")
with open(os.path.join(os.path.dirname(__file__), "..", "interface", "index.html"), encoding="utf-8") as _f:
    _src_ui = _f.read()
check("setInterval(() => majVerifieMaj(false)" in _src_ui, "front : re-vérification périodique (bannière seule)")
check("veilleServeur" in _src_ui and "location.reload()" in _src_ui,
      "front : watchdog serveur -> rechargement auto quand la MAJ est finie (page plus jamais figée)")
check("Relance Provara.exe" in _src_ui, "front : consigne actionnable si l'app ne revient pas (échec DLL/AV)")
_src_maj = inspect.getsource(maj._lance_updater)
check("IMAGENAME eq Provara.exe" in _src_maj and _src_maj.count("start") >= 2,
      "updater : re-lancement de secours si l'app n'a pas démarré (antivirus/DLL au 1er départ)")

print("=== valide_maj : %d/%d ===" % (_ok[0], _ok[0] + _ko[0]))
sys.exit(0 if _ko[0] == 0 else 1)
