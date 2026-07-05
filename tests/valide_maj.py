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

print("=== valide_maj : %d/%d ===" % (_ok[0], _ok[0] + _ko[0]))
sys.exit(0 if _ko[0] == 0 else 1)
