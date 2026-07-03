"""VALIDE l'ingestion des COORDONNÉES (ingere_coordonnees.py) + le câblage ia (coordonnees_lieu / distance_lieux /
cap_lieux) — ADVERSE, FAUX=0.

Trois familles de garanties :
  1) ANCRES EXTERNES non circulaires : la coordonnée ingérée d'une capitale connue tombe à <0,05° de sa position
     de référence (Paris, Tokyo, Washington, Canberra…) — jamais une valeur inventée / lon⇄lat inversés.
  2) CÂBLAGE : distance_lieux reproduit des distances orthodromiques publiées (Paris→Londres ≈344, Paris→Moscou
     ≈2486 km), est symétrique, et cap_lieux reste dans [0,360[.
  3) SOUNDNESS : lieu inconnu -> None (HORS, jamais deviné) ; TOUTE latitude ingérée ∈ [-90,90], longitude ∈
     [-180,180] ; les tables latitude_* et longitude_* ont exactement les mêmes clés (pas de coordonnée bancale).
"""
import json
import os

import ia

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


# ── 1) ANCRES EXTERNES (position de référence, non circulaire) — via le vrai chemin ia.coordonnees_lieu ──
ANCRES = {
    "Paris": (48.857, 2.352), "Londres": (51.507, -0.128), "Tokyo": (35.689, 139.692),
    "Washington": (38.895, -77.037), "Canberra": (-35.293, 149.127), "Moscou": (55.751, 37.618),
    "Le Caire": (30.044, 31.236), "Brasilia": (-15.794, -47.883), "Wellington": (-41.289, 174.777),
    "Ottawa": (45.425, -75.695),
}
for nom, (lat_ref, lon_ref) in ANCRES.items():
    c = ia.coordonnees_lieu(nom)
    check(c is not None, f"{nom} : coordonnée présente")
    if c is not None:
        check(abs(c[0] - lat_ref) < 0.05, f"{nom} latitude ≈ {lat_ref} (obtenu {c[0]})")
        check(abs(c[1] - lon_ref) < 0.05, f"{nom} longitude ≈ {lon_ref} (obtenu {c[1]})")

# ── 2) CÂBLAGE : distances orthodromiques publiées + symétrie + cap ──
d_pl = ia.distance_lieux("Paris", "Londres")
check(d_pl is not None and abs(d_pl - 344.0) <= 0.03 * 344.0, f"Paris→Londres ≈344 km (obtenu {d_pl})")
d_pm = ia.distance_lieux("Paris", "Moscou")
check(d_pm is not None and abs(d_pm - 2486.0) <= 0.03 * 2486.0, f"Paris→Moscou ≈2486 km (obtenu {d_pm})")
check(ia.distance_lieux("Paris", "Londres") == ia.distance_lieux("Londres", "Paris"), "distance symétrique")
check(ia.distance_lieux("Tokyo", "Tokyo") == 0.0, "distance d'un lieu à lui-même = 0")
cap = ia.cap_lieux("Paris", "Londres")
check(cap is not None and 325.0 <= cap <= 335.0, f"cap Paris→Londres ~330° NO (obtenu {cap})")
check(cap is None or 0.0 <= cap < 360.0, "cap dans [0,360)")

# ── 3) SOUNDNESS : lieu inconnu -> None (HORS) ──
BIDON = "Zzyzx-Ville-Inexistante-42"
check(ia.coordonnees_lieu(BIDON) is None, "lieu inconnu -> coordonnées None (HORS)")
check(ia.distance_lieux("Paris", BIDON) is None, "distance vers lieu inconnu -> None (HORS)")
check(ia.distance_lieux(BIDON, "Paris") is None, "distance depuis lieu inconnu -> None (HORS)")
check(ia.cap_lieux("Paris", BIDON) is None, "cap vers lieu inconnu -> None (HORS)")

# ── 3bis) BORNES + COHÉRENCE sur TOUTE la table ingérée (lecture directe du jsonl, exhaustif) ──
DOSSIER = os.path.join(os.path.dirname(__file__), "datasets", "lecteur")


def _charge(rel):
    d = {}
    chemin = os.path.join(DOSSIER, rel + ".jsonl")
    if not os.path.exists(chemin):
        return d
    for ligne in open(chemin, encoding="utf-8"):
        o = json.loads(ligne)
        if "entite" in o:
            d[o["entite"]] = o["valeur"]
    return d


lat_t = _charge("latitude_capitale")
lon_t = _charge("longitude_capitale")
check(len(lat_t) > 150, f"table latitude_capitale peuplée ({len(lat_t)} entrées)")
check(set(lat_t) == set(lon_t), "clés latitude == clés longitude (pas de coordonnée bancale)")
hors_borne = 0
for nom, v in lat_t.items():
    if not (-90.0 <= float(v) <= 90.0):
        hors_borne += 1
for nom, v in lon_t.items():
    if not (-180.0 <= float(v) <= 180.0):
        hors_borne += 1
check(hors_borne == 0, f"toutes les coordonnées dans les bornes (violations : {hors_borne})")

print(f"\n=== valide_coordonnees : {ok}/{ok + ko} ===")
import sys

sys.exit(0 if ko == 0 else 1)
