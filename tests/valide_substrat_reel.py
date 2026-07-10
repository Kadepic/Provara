"""VALIDE substrat_reel.py — le gap-engine d'invention branché sur les 71 M faits, FAUX=0.

Oracle indépendant (anti-faux-positif) : pour TOUTE invention émise, on re-suit le chemin témoin arête par arête et on
EXIGE que `graphe_monde.verifie_chemin` le confirme — une invention dont le témoin ne re-vérifie pas serait un faux.
Test-clé de soundness : le composite HOMONYME (capitale∘pays_subdivision via « victoria ») DOIT être REJETÉ
(couverture faible), pas émis comme invention. Négatifs : type/relation inconnus -> ValueError.

⚠ Lourd : charge le lecteur complet (71 M faits). Une seule instance à la fois.
"""
# ─── GARDE « BASE COMPLÈTE » (2026-07-12) — SKIP propre sur l'échantillon ───
# Gate de classe BASE RÉELLE (72 M). Sur l'échantillon committé (que _nonreg épingle) sa donnée est
# absente et ses ancres tomberaient en FAUX-échec. Marqueur de base réelle : occupation_personne (2,35 M,
# jamais committé). Base réelle vérifiée par la passe manuelle valide_lecteur* (cf. CHANGELOG). Une gate
# honnête SKIPPE quand sa donnée manque, elle ne tombe pas.
import os as _os, sys as _sys
_bc = _os.environ.get("LECTEUR_DATASETS_DIR")
if _bc and not _os.path.exists(_os.path.join(_bc, "occupation_personne.jsonl")):
    print("=== valide_substrat_reel : SKIP — base complète requise (occupation_personne absent de ce store) ===")
    _sys.exit(0)
# ──────────────────────────────────────────────────────

import graphe_monde
import substrat_reel as SR

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


def _pont_est_entite(pont):
    """Un pont émis doit passer la garde entité-typée (codomaine d'entité + domaine incluant 'pays')."""
    return SR._pont_valide(pont, "pays")


# ── T0 : transducteurs typés dérivés du réel ──
T = SR.transducteurs_reels(min_taille=50)
check(len(T) >= 3, f"transducteurs dérivés du réel (vu {len(T)})")
paires = {(a, b) for _, a, b in T}
check(any(rel == "capitale" and a == "pays" for rel, a, b in T), "transducteur réel : capitale (pays -> ville/capitale)")
check(all(a != b for _, a, b in T), "transducteurs : arêtes non triviales (type change)")

# ── T1 : connus_reel = paires réalisées en direct ──
connus = SR.connus_reel(T)
check(("pays", "villes") in connus or ("pays", "capitales") in connus, "connus_reel : pays->ville réalisé en direct")

# ── T3 : examine_reel — relation directe -> EXISTE_DEJA ──
type_ville = "capitales" if ("pays", "capitales") in connus else "villes"
ex = SR.examine_reel("pays", type_ville, T)
check(ex.statut == SR.EXISTE_DEJA, f"examine_reel(pays->{type_ville}) = EXISTE_DEJA (relation directe)")

# ── derive_attribut : le cœur de l'objectif final ──
inv = SR.derive_attribut("pays", "population_ville", budget=200)
check(inv.statut == SR.INVENTION, "population de la capitale : INVENTION")
check(inv.pont == "capitale" and inv.cible == "population_ville", "invention = capitale ∘ population_ville")

# ORACLE ANTI-FAUX-POSITIF : le témoin re-vérifie arête par arête (indépendamment)
e0, mi, val = inv.temoin
check(graphe_monde.verifie_chemin(e0, [(inv.pont, mi), (inv.cible, val)]),
      "témoin de l'invention re-vérifié par graphe_monde (chemin réel)")

# EXISTE_DEJA : un attribut direct n'est pas une invention
dej = SR.derive_attribut("pays", "capitale", budget=150)
check(dej.statut == SR.EXISTE_DEJA, "capitale (attribut direct) -> EXISTE_DEJA, pas invention")

# ── TEST-CLÉ FAUX=0 : le composite HOMONYME est REJETÉ (couverture faible) ──
hom = SR.derive_attribut("pays", "pays_subdivision", budget=200)
check(hom.statut == SR.BRIQUE_MANQUANTE, "homonyme (capitale∘pays_subdivision, « victoria ») REJETÉ = BRIQUE_MANQUANTE")
check(hom.pont == "" and len(hom.justification) > 10, "rejet homonyme tracé (aucun pont systématique retenu)")

# ── composites_utiles : tous INVENTION, tous témoins re-vérifiés ──
comps = SR.composites_utiles("pays", budget=150, k=8)
check(len(comps) >= 3, f"composites_utiles(pays) -> plusieurs inventions (vu {len(comps)})")
check(all(c.statut == SR.INVENTION for c in comps), "tous les composites retournés sont INVENTION")
tous_verifies = all(graphe_monde.verifie_chemin(c.temoin[0], [(c.pont, c.temoin[1]), (c.cible, c.temoin[2])])
                    for c in comps)
check(tous_verifies, "TOUS les témoins des composites re-vérifient (0 faux positif)")
check(all(_pont_est_entite(c.pont) for c in comps), "composites de 'pays' passent par des ponts entité-typés (capitale/point_culminant…)")
check(not any(c.pont in ("sans_littoral",) for c in comps), "aucun composite via une relation booléenne (garde entité vs scalaire)")

# ── TYPES ENRICHIS : l'univers de types dépasse les 5 de taxonomie (personnes/œuvres/films…) ──
types = SR.types_reels()
check({"personnes", "oeuvres_ecrites", "films"} <= set(types), "types enrichis présents (personnes/œuvres/films)")
check(len(types) >= 10, f"univers de types étendu (vu {len(types)})")

# ── composite ENRICHI utile : année de naissance de l'auteur d'une œuvre (pivot = une personne) ──
aut = SR.derive_attribut("oeuvres_ecrites", "annee_naissance_personne", budget=200)
check(aut.statut == SR.INVENTION, "année de naissance de l'auteur : INVENTION")
check(aut.pont == "auteur_oeuvre_ecrite" and aut.cible == "annee_naissance_personne", "invention = auteur ∘ année_naissance")
check(graphe_monde.verifie_chemin(aut.temoin[0], [(aut.pont, aut.temoin[1]), (aut.cible, aut.temoin[2])]),
      "témoin de l'invention enrichie re-vérifié (chemin réel œuvre→auteur→année)")
comps_o = SR.composites_utiles("oeuvres_ecrites", budget=120, k=6)
check(len(comps_o) >= 3 and all(c.statut == SR.INVENTION for c in comps_o), "composites_utiles(œuvres) -> plusieurs inventions")
check(all(graphe_monde.verifie_chemin(c.temoin[0], [(c.pont, c.temoin[1]), (c.cible, c.temoin[2])]) for c in comps_o),
      "tous les témoins (œuvres) re-vérifient (0 faux positif sur type enrichi)")

# ── FAUX=0 : entrées invalides -> ValueError ──
check(leve(SR.derive_attribut, "pays", "relation_inexistante_xyz"), "relation cible inconnue -> ValueError")
check(leve(SR._echantillon_type, "type_bidon_xyz", 10), "type source inconnu -> ValueError")

print(f"\n=== valide_substrat_reel : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
