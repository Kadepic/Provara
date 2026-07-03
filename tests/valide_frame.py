"""
VALIDATION du FRAME N-AIRE (frame.py) — Vague 1.
FAUX=0 : rôle requis manquant -> invalide (détecté) ; rôle hors schéma -> RoleInconnu ; rôle absent -> None (jamais inventé).
"""
from __future__ import annotations

from frame import Frame, RoleInconnu, register_schema, SCHEMAS

ok = 0
total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}", flush=True)
    if cond:
        ok += 1
    else:
        raise AssertionError(nom)


def leve(fn, exc):
    try:
        fn(); return False
    except exc:
        return True


# ── Frame valide + accès aux rôles ───────────────────────────────────────────────────────
f = Frame("transfert", {"quoi": "chaleur", "source": "intérieur", "cible": "extérieur", "mecanisme": "pompe"})
check("frame valide (tous les requis présents)", f.valide() and f.roles_manquants() == [])
check("accès rôle rempli", f.role("source") == "intérieur")
check("accès rôle absent -> None (jamais inventé)", f.role("température") is None)
check("type conservé", f.type == "transfert")

# ── Rôle requis manquant -> invalide (détecté, pas caché) ────────────────────────────────
g = Frame("cause", {"cause": "friction"})          # 'effet' requis manquant
check("requis manquant -> invalide", not g.valide() and "effet" in g.roles_manquants())

# ── Rôle hors schéma -> REJET FAUX=0 ─────────────────────────────────────────────────────
check("rôle hors schéma -> RoleInconnu",
      leve(lambda: Frame("cause", {"cause": "a", "effet": "b", "couleur": "rouge"}), RoleInconnu))

# ── Open-vocab (type sans schéma) : libre mais inspectable ───────────────────────────────
libre = Frame("bricolage_maison", {"x": 1, "y": 2})
check("type sans schéma : accepté et valide (open-vocab)", libre.valide() and libre.role("x") == 1)

# ── Nesting : un filler peut être un autre frame ─────────────────────────────────────────
mecanisme = Frame("transition", {"systeme": "eau", "de": "liquide", "vers": "gaz", "action": "chauffage"})
cause = Frame("cause", {"cause": "apport d'énergie", "effet": "évaporation", "mecanisme": mecanisme})
check("nesting : rôle = frame imbriqué", isinstance(cause.role("mecanisme"), Frame)
      and cause.role("mecanisme").role("vers") == "gaz")

# ── Pont binaire <-> frame ───────────────────────────────────────────────────────────────
b = Frame.depuis_binaire("capitale", "France", "Paris")
check("réification d'un triplet plat", b.role("sujet") == "France" and b.role("objet") == "Paris")
check("décomposition en triplets", ("capitale", "sujet", "France") in b.vers_binaires())

# ── register_schema + immuabilité + égalité ──────────────────────────────────────────────
register_schema("refroidissement", requis=("cible", "methode"), optionnels=("puissance",))
r = Frame("refroidissement", {"cible": "pièce", "methode": "radiatif"})
check("schéma enregistré à chaud fonctionne", r.valide() and "refroidissement" in SCHEMAS)
check("rôle hors nouveau schéma rejeté",
      leve(lambda: Frame("refroidissement", {"cible": "x", "methode": "y", "z": 1}), RoleInconnu))
check("égalité structurelle de deux frames identiques",
      Frame("cause", {"cause": "a", "effet": "b"}) == Frame("cause", {"effet": "b", "cause": "a"}))
check("hachable (utilisable en set/clé)", len({f, f, g}) == 2)

# ── RÉIFICATION SÛRE : round-trip multi-frames FIDÈLE (durcissement FAUX=0, 2026-07-02) ───────────────
# Le défaut latent : vers_binaires() perd l'id d'instance -> deux frames de même type fusionnent leurs rôles
# à la relecture. vers_triplets(id)/depuis_triplets réifient avec un id unique -> reconstruction fidèle, jamais
# de fusion. C'est le PRÉREQUIS FAUX=0 avant tout stockage/relecture de frames dans un bac plat commun.
c1 = Frame("cause", {"cause": "friction", "effet": "chaleur"})
c2 = Frame("cause", {"cause": "gel", "effet": "fissure"})            # MÊME type, rôles DIFFÉRENTS
plat = c1.vers_triplets("evt1") + c2.vers_triplets("evt2")          # aplatis dans un MÊME bac plat
recon = Frame.depuis_triplets(plat)
check("RÉIFICATION : round-trip multi-frames fidèle (2 frames reconstruits)", len(recon) == 2)
check("RÉIFICATION FAUX=0 : aucune fusion de rôles (evt1=friction->chaleur)",
      recon["evt1"] == c1 and recon["evt1"].role("cause") == "friction" and recon["evt1"].role("effet") == "chaleur")
check("RÉIFICATION FAUX=0 : instances séparées (evt2=gel->fissure, pas mélangé avec evt1)",
      recon["evt2"] == c2 and recon["evt2"].role("cause") == "gel")
check("RÉIFICATION : id obligatoire (unicité = garde FAUX=0)",
      leve(lambda: c1.vers_triplets(""), ValueError) and leve(lambda: c1.vers_triplets(None), ValueError))
check("RÉIFICATION FAUX=0 : conflit de rôle à la relecture -> ValueError (jamais un choix silencieux)",
      leve(lambda: Frame.depuis_triplets([("e", Frame.TYPE_ROLE, "cause"), ("e", "cause", "a"), ("e", "cause", "b")]),
           ValueError))
check("RÉIFICATION FAUX=0 : groupe sans type ignoré (on ne fabrique pas un frame sans type)",
      Frame.depuis_triplets([("e", "cause", "a"), ("e", "effet", "b")]) == {})
check("RÉIFICATION : rôle réservé __type__ interdit comme rôle métier",
      leve(lambda: Frame("cause", {"cause": "a", "effet": "b", "__type__": "x"}).vers_triplets("z"), RoleInconnu)
      or leve(lambda: Frame("bricolage", {"__type__": "x"}).vers_triplets("z"), RoleInconnu))

# ── SCHÉMA ÉVÉNEMENT neo-davidsonien (agent/patient/instrument/temps/lieu) ────────────────────────────
ev = Frame("evenement", {"predicat": "ouvrir", "agent": "Marie", "patient": "porte",
                         "instrument": "clé", "temps": "hier", "lieu": "maison"})
check("ÉVÉNEMENT : frame neo-davidsonien valide (predicat+agent requis)", ev.valide())
check("ÉVÉNEMENT : rôles thématiques accessibles (agent/patient/instrument)",
      ev.role("agent") == "Marie" and ev.role("patient") == "porte" and ev.role("instrument") == "clé")
check("ÉVÉNEMENT FAUX=0 : agent requis manquant -> invalide",
      not Frame("evenement", {"predicat": "tomber"}).valide())
check("ÉVÉNEMENT FAUX=0 : rôle thématique fantaisiste rejeté",
      leve(lambda: Frame("evenement", {"predicat": "p", "agent": "a", "couleur": "rouge"}), RoleInconnu))

print(f"\n=== valide_frame : {ok}/{total} checks OK ===")
if ok != total:
    raise SystemExit(1)
