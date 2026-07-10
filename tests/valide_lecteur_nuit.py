"""Validateur FAUX=0 des veines ingérées pendant la NUIT autonome 2026-06-29 (Levier 3 harvester).
Extensible : chaque veine = (relation, ratio_max_fermeture, valeurs-noyau, ancres vérité-terrain, adversaire).
Pattern frugal : amorce-seule (jamais le global) + cache mmap .colf (chargement quasi-gratuit, par relation).
FAUX=0 : table fermée (ratio bas), valeurs sensées, noyau présent, ANCRES exactes (vérité indépendante,
non-circulaire), adversaire -> HORS. Lance seul : `python3 valide_lecteur_nuit.py`."""
# ─── GARDE « BASE COMPLÈTE » (2026-07-12) — SKIP propre sur l'échantillon ───
# Gate de classe BASE RÉELLE (72 M). Sur l'échantillon committé (que _nonreg épingle) sa donnée est
# absente et ses ancres tomberaient en FAUX-échec. Marqueur de base réelle : occupation_personne (2,35 M,
# jamais committé). Base réelle vérifiée par la passe manuelle valide_lecteur* (cf. CHANGELOG). Une gate
# honnête SKIPPE quand sa donnée manque, elle ne tombe pas.
import os as _os, sys as _sys
_bc = _os.environ.get("LECTEUR_DATASETS_DIR")
if _bc and not _os.path.exists(_os.path.join(_bc, "occupation_personne.jsonl")):
    print("=== valide_lecteur_nuit : SKIP — base complète requise (occupation_personne absent de ce store) ===")
    _sys.exit(0)
# ──────────────────────────────────────────────────────

from garde_ressources import borne
borne(max_go=4.0, max_cpu_s=900)   # veines DATE millionnaires (naissance 3,2M) chargées par relation (fresh Lecteur)

import json
import os
import re
import sys

os.environ.setdefault("LECTEUR_AMORCE_SEULE", "1")   # jamais le full-load global
import lecteur as L
from base_faits import normalise as _norm

_DS = os.environ.get("LECTEUR_DATASETS_DIR") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datasets", "lecteur")
_ECHECS = []


def check(cond, msg):
    print(f"  [{'OK ' if cond else 'FAIL'}] {msg}")
    if not cond:
        _ECHECS.append(msg)


def _charge(lec, relation):
    chemin = os.path.join(_DS, relation + ".jsonl")
    if not os.path.exists(chemin):
        check(False, f"{relation} : dataset absent ({chemin})")
        return None
    mct, _mrel, mart = L._charge_colf_mmap(relation + ".jsonl", chemin)   # chemin rapide mmap
    if mct is not None:
        lec.tables[relation] = mct
        lec.norm_articles.setdefault(relation, mart)
        return mct
    with open(chemin, encoding="utf-8") as fh:
        tete = json.loads(fh.readline())
    lec.charge_jsonl(relation, chemin, tete.get("_categorie", "convention"),
                     tete.get("_source", "nuit"), articles=bool(tete.get("_articles", True)))
    return lec.tables.get(relation)


# (relation, ratio_max, valeurs-noyau, ancres [(entité, valeur attendue)], entité-adversaire)
VEINES = [
    ("technique_creation_peinture", 0.10,
     ["peinture à l'huile", "fresque", "aquarelle", "gouache", "grisaille"],
     [("L'École d'Athènes", "fresque"),
      ("plafond de la chapelle Sixtine", "fresque"),
      ("Les glaneuses", "peinture à l'huile"),
      ("Les licteurs rapportant à Brutus les corps de ses fils", "peinture à l'huile")],
     "oeuvre-peinte-inexistante-zzz"),
]


def valide(lec, spec):
    relation, ratio_max, core, ancres, adv = spec
    t = _charge(lec, relation)
    if t is None:
        return
    n = len(t)
    vals = [f.valeur for f in t.values()]
    dist = set(vals)
    ratio = len(dist) / n if n else 1.0
    print(f"-- {relation} : {n} entités, {len(dist)} valeurs distinctes, ratio={ratio:.3f}")
    check(n > 0, f"{relation} : table non vide")
    check(ratio <= ratio_max, f"{relation} : fermeture OK (ratio {ratio:.3f} ≤ {ratio_max})")
    check(all(len(v.strip()) >= 2 and any(c.isalpha() for c in v) for v in dist),
          f"{relation} : toutes les valeurs ≥2 car. avec lettre")
    pres = {_norm(v) for v in dist}
    trouve = [c for c in core if _norm(c) in pres]
    check(len(trouve) >= min(3, len(core)),
          f"{relation} : contrôle positif {len(trouve)}/{len(core)} valeurs-noyau ({trouve[:4]})")
    ok = 0
    for ent, att in ancres:
        fr = lec.cherche(relation, ent)
        bon = fr is not None and _norm(fr.valeur) == _norm(att)
        if not bon:
            print(f"     ancre RATÉE : {ent!r} -> {(fr.valeur if fr else 'HORS')!r} (attendu {att!r})")
        ok += bon
    check(ok == len(ancres), f"{relation} : {ok}/{len(ancres)} ancres vérité-terrain exactes")
    st, _ = lec.repond(relation, adv)
    check(st == L.HORS, f"{relation} : adversaire « {adv} » -> HORS")


# Veines DATE (valeurs = années signées, pas un ensemble fermé à lettres) :
# (relation, (annee_min, annee_max), ancres [(personne, année)], entité-adversaire)
_AN_RE = re.compile(r"^-?\d{1,4}$")
DATE_VEINES = [
    ("annee_naissance_personne", (-4000, 2026),
     [("Napoléon Ier", "1769"), ("Albert Einstein", "1879"), ("Marie Curie", "1867"),
      ("Nicolas Copernic", "1473"), ("Jean-Sébastien Bach", "1685")],
     "personne-totalement-inexistante-zzz-nuit"),
    ("annee_deces_personne", (-4000, 2026),
     [("Napoléon Ier", "1821"), ("Albert Einstein", "1955"), ("Marie Curie", "1934")],
     "personne-totalement-inexistante-zzz-nuit"),
    ("annee_publication_oeuvre", (-3000, 2026),
     [("The Dark Side of the Moon", "1973"), ("OK Computer", "1997"),
      ("Abbey Road", "1969"), ("Random Access Memories", "2013")],
     "oeuvre-totalement-inexistante-zzz-nuit"),
    ("annee_construction_edifice", (-4000, 2026),
     [("Empire State Building", "1931"), ("opéra de Sydney", "1973"),
      ("tour de Pise", "1173"), ("Tower Bridge", "1886"), ("British Museum", "1753")],
     "edifice-totalement-inexistant-zzz-nuit"),
    ("annee_ouverture_edifice", (-4000, 2026),
     [("Burj Khalifa", "2010"), ("Tower Bridge", "1894"), ("tour Eiffel", "1889")],
     "edifice-totalement-inexistant-zzz-nuit-2"),
    ("annee_decouverte_astre", (-4000, 2026),
     [("(1) Cérès", "1801"), ("(4) Vesta", "1807"), ("(433) Éros", "1898")],
     "astre-totalement-inexistant-zzz-nuit"),
    ("annee_creation_oeuvre_art", (-4000, 2026),
     [("La Persistance de la mémoire", "1931"), ("Nighthawks", "1942"),
      ("Le Fils de l'homme", "1964"), ("Composition VIII", "1923"),
      ("La Liberté guidant le peuple", "1830")],
     "oeuvre-art-totalement-inexistante-zzz-nuit"),
]


def valide_date(lec, spec):
    relation, (lo, hi), ancres, adv = spec
    t = _charge(lec, relation)
    if t is None:
        return
    n = len(t)
    vals = {f.valeur for f in t.values()}
    print(f"-- {relation} : {n} entités, {len(vals)} années distinctes")
    check(n > 0, f"{relation} : table non vide")
    bad = [v for v in vals if not _AN_RE.match(v) or not (lo <= int(v) <= hi)]
    check(not bad, f"{relation} : toutes les valeurs sont des années dans [{lo},{hi}] (contre-ex {bad[:5]})")
    ok = 0
    for ent, att in ancres:
        fr = lec.cherche(relation, ent)
        bon = fr is not None and fr.valeur == att
        if not bon:
            print(f"     ancre RATÉE : {ent!r} -> {(fr.valeur if fr else 'HORS')!r} (attendu {att!r})")
        ok += bon
    check(ok == len(ancres), f"{relation} : {ok}/{len(ancres)} ancres vérité-terrain exactes")
    st, _ = lec.repond(relation, adv)
    check(st == L.HORS, f"{relation} : adversaire « {adv} » -> HORS")


def main():
    cibles = set(sys.argv[1:])
    veines = [v for v in VEINES if not cibles or v[0] in cibles]
    for spec in veines:
        valide(L.Lecteur(), spec)
    dveines = [v for v in DATE_VEINES if not cibles or v[0] in cibles]
    for spec in dveines:
        valide_date(L.Lecteur(), spec)
    print()
    if _ECHECS:
        print(f"ÉCHEC : {len(_ECHECS)} check(s) en échec.")
        return 1
    print(f"OK : NUIT — {len(veines) + len(dveines)} veine(s) validée(s) FAUX=0.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
