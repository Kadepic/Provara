#!/usr/bin/env python3
"""VALIDE l'ingestion coordonnées des LOCALITÉS (Wikidata/QLever P625, portée Q486972) + câblage navigation — ADVERSE, FAUX=0.

Cycle 2 de la géo (après les capitales) : villes/communes/villages au NOM GLOBALEMENT UNIQUE.

Ancres EXTERNES non circulaires (villes NON capitales connues, présentes car nom unique) via le vrai chemin
`ia.coordonnees_lieu`. GARDE ANTI-HOMONYME jugée adversairement : un nom porté par ≥2 localités (Bordeaux/Nantes/
Strasbourg ont des homonymes US à libellé FR ; Brest FR vs BY ; Cordoue ES vs AR) est ABSENT (jamais tranché).
Soundness : lieu inconnu -> None. Bulk : bornes lat/lon globales, clés jumelles alignées, volume attendu.
"""
import json
import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__)) or "."
sys.path.insert(0, _ICI)
sys.path.insert(0, os.path.join(_ICI, "interface"))

import ia
import repond as _REP

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


# ── ANCRES EXTERNES : villes uniques présentes, coords vérifiées indépendamment (tolérance 0,3° ≈ 33 km) ──
ANCRES = {
    "Toulouse": (43.60, 1.44), "Barcelone": (41.39, 2.16), "Hambourg": (53.55, 9.99),
    "Marrakech": (31.63, -8.01), "Fukuoka": (33.59, 130.40), "Édimbourg": (55.95, -3.19),
    "Wuhan": (30.59, 114.30), "Chengdu": (30.66, 104.06), "Bangalore": (12.98, 77.59),
    "Göteborg": (57.71, 11.97), "Grenoble": (45.19, 5.73), "Reykjavik": (64.15, -21.94),
    "Katmandou": (27.71, 85.32),
}
for nom, (la, lo) in ANCRES.items():
    c = ia.coordonnees_lieu(nom)
    check(c is not None, f"{nom} : coordonnées présentes (nom unique)")
    if c is not None:
        check(abs(c[0] - la) < 0.3 and abs(c[1] - lo) < 0.3,
              f"{nom} : ({c[0]:.3f}, {c[1]:.3f}) ≈ ancre externe ({la}, {lo})")

# ── GARDE ANTI-HOMONYME (soundness du crible) : un nom mondialement ambigu -> ABSENT (jamais un mauvais point) ──
# NB : ces noms peuvent exister comme CAPITALE (portée non ambiguë, servie ailleurs) — on teste des non-capitales.
HOMONYMES = ["Bordeaux", "Nantes", "Strasbourg", "Cordoue", "Springfield", "Melbourne", "Brest", "Milan"]
for h in HOMONYMES:
    # absent des LOCALITÉS ; s'il répond, ce doit être une capitale (jamais un homonyme arbitraire tranché).
    c = ia.coordonnees_lieu(h)
    check(c is None or h in {"Tripoli"},  # aucun de la liste n'est capitale -> tous doivent être None
          f"homonyme « {h} » -> None (garde anti-homonyme : jamais un point arbitraire)")

# ── SOUNDNESS : lieu inexistant -> None ──
check(ia.coordonnees_lieu("Ville-Qui-N-Existe-Pas-4242") is None, "lieu inconnu -> None (HORS)")
check(ia.coordonnees_lieu("") is None, "lieu vide -> None (HORS)")

# ── CÂBLAGE navigation : distance & cap sur des villes présentes (valeurs publiées, tolérance large) ──
d = ia.distance_lieux("Toulouse", "Barcelone")
check(d is not None and 240 < d < 300, f"distance Toulouse–Barcelone ≈ 245–290 km (obtenu {d})")
d2 = ia.distance_lieux("Barcelone", "Toulouse")
check(d is not None and d2 is not None and abs(d - d2) < 1e-6, "distance symétrique")
cap = ia.cap_lieux("Toulouse", "Barcelone")
check(cap is not None and 0 <= cap < 360, f"cap Toulouse->Barcelone dans [0,360) (obtenu {cap})")

# ── BULK : les deux tables jumelles saines (relues indépendamment) ──
DOSSIER = os.path.join(_ICI, "datasets", "lecteur")


def _charge(rel):
    d = {}
    for ligne in open(os.path.join(DOSSIER, rel + ".jsonl"), encoding="utf-8"):
        o = json.loads(ligne)
        if "entite" in o:
            d[o["entite"]] = o["valeur"]
    return d


lat = _charge("latitude_localite")
lon = _charge("longitude_localite")
check(len(lat) > 200_000, f"latitude_localite peuplée ({len(lat)} localités)")
check(set(lat) == set(lon), "clés latitude/longitude EXACTEMENT alignées (paires complètes)")
try:
    check(all(-90.0 <= float(v) <= 90.0 for v in lat.values()), "toutes les latitudes dans [-90, 90]")
    check(all(-180.0 <= float(v) <= 180.0 for v in lon.values()), "toutes les longitudes dans [-180, 180]")
except ValueError:
    check(False, "toutes les coordonnées sont des nombres")
# une localité au moins dans chaque hémisphère (couverture mondiale plausible, pas un dump biaisé)
lats = [float(v) for v in lat.values()]
lons = [float(v) for v in lon.values()]
check(any(v > 0 for v in lats) and any(v < 0 for v in lats), "couverture N et S")
check(any(v > 0 for v in lons) and any(v < 0 for v in lons), "couverture E et O")

# ── LOCALISATION NL « où se trouve X » -> coords verbalisées (repond._localisation), SOUND ──
loc = _REP._localisation("Où se trouve Toulouse ?")
check(loc is not None and "43.6" in loc and "1.44" in loc and "°N" in loc,
      f"« où se trouve Toulouse » -> coords vérifiées verbalisées (obtenu {loc!r})")
loc = _REP._localisation("coordonnées de Barcelone")
check(loc is not None and "41.38" in loc, "« coordonnées de Barcelone » -> coords verbalisées")
check(_REP._localisation("Où se trouve Ville-Inexistante-4242 ?") is None,
      "localisation d'un lieu inconnu -> None (HORS honnête, jamais deviné)")
check(_REP._localisation("Où en es-tu ?") is None, "« où en es-tu » (non locationnel) -> None (pas de faux match)")
check(_REP._localisation("Quelle est la capitale de la France ?") is None,
      "question non-locationnelle -> None (pas de capture abusive)")

print(f"\n=== valide_villes_coordonnees : {ok}/{ok + ko} ===")
sys.exit(0 if ko == 0 else 1)
