# -*- coding: utf-8 -*-
"""VALIDE la CARTE DES SUJETS (sujets.py) et son MOTEUR DE COUVERTURE (couverture_borne.py) — reconstruits
2026-07-10 sur mandat Yohan. FAUX=0 : aucune preuve n'est CRUE, chacune est vérifiée sur le disque ; zéro
dette tolérée (une preuve déclarée introuvable fait ROUGIR la gate) ; le non-borné n'est jamais « traité »
par une réponse, seulement par le routage honnête.

Le fichier auto (SUJETS_ANNEXES_AUTO.md, ~83k sujets métiers×axes) est DÉRIVABLE et gitignoré : la gate
fonctionne avec ou sans lui (elle mesure ce qui est là, et le dit)."""
from __future__ import annotations

import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__)) or "."
sys.path.insert(0, os.path.join(os.path.dirname(_ICI), "src"))

import sujets as S
import couverture_borne as C

ok = ko = 0


def check(c, label):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print("  FAIL: " + label)


# ── le document committé se parse et couvre les grandes parties ──
tous = S.charge()
check(len(tous) >= 1500, "document committé : ≥ 1500 sujets (%d)" % len(tous))
parties = {s.partie.split("—")[0].strip() for s in tous}
check(len([p for p in parties if p.startswith("PARTIE")]) >= 12,
      "≥ 12 parties conceptuelles (%d)" % len([p for p in parties if p.startswith("PARTIE")]))
check(any(p.startswith("ANNEXE S") for p in parties), "annexe S (store) présente")
check(any(p.startswith("ANNEXE T") for p in parties), "annexe T (taxonomies hors-Wikidata) présente")

# ── tous les codes sont légaux ; les bornés dominent mais le non-borné est CARTOGRAPHIÉ ──
check(all(s.code in S.CODES for s in tous), "tous les codes de bornage sont légaux")
check(sum(1 for s in tous if s.borne) >= 1400, "≥ 1400 sujets bornés dans le document committé")
check(sum(1 for s in tous if s.non_borne) >= 20, "le non-borné est cartographié (≥ 20 sujets)")
check(any(s.code == "NB-INDEC" for s in tous) and any(s.code == "NB-OUV" for s in tous),
      "les deux natures d'ignorance sont distinguées (indécidable vs science ouverte)")

# ── les sujets du store correspondent VRAIMENT à des tables (pas d'invention) ──
store = os.environ.get("LECTEUR_DATASETS_DIR", "")
sujets_store = [s.libelle.split(" : ", 1)[1] for s in tous if s.partie.startswith("ANNEXE S")]
check(len(sujets_store) >= 1000, "annexe S : ≥ 1000 tables (%d)" % len(sujets_store))
if store and os.path.isdir(store):
    reelles = {f[:-6] for f in os.listdir(store) if f.endswith(".jsonl")}
    carte = set(sujets_store)
    # SENS D'INCLUSION SOUND : la carte doit COUVRIR le store pointé (aucune table réelle sans sujet).
    # L'inverse serait faux sur l'ÉCHANTILLON embarqué (sous-ensemble de la base complète) : la carte est
    # générée depuis la base COMPLÈTE, elle contient légitimement des tables absentes de l'échantillon.
    non_couvertes = sorted(reelles - carte)
    check(not non_couvertes,
          "chaque table RÉELLE du store pointé a son sujet dans la carte (%d non couvertes : %s)"
          % (len(non_couvertes), non_couvertes[:3]))
    if len(reelles) >= len(carte):                       # base complète pointée -> l'égalité est exigible
        check(carte <= reelles, "sur la base complète : aucun sujet-store orphelin (%d)" % len(carte - reelles))
    else:
        check(True, "(échantillon pointé : %d tables ⊂ carte de %d — inclusion vérifiée)" % (len(reelles), len(carte)))
else:
    check(True, "(store non pointé : vérification des tables sautée — LECTEUR_DATASETS_DIR)")

# ── le moteur de couverture : mesuré, jamais déclaré ──
r = C.rapport(tous)
check(r["total"] == len(tous), "rapport : total cohérent")
check(r[C.TRAITE] + r[C.PARTIEL] + r[C.NON_TRAITE] == r["total"], "partition exacte des trois états")
check(r[C.TRAITE] >= 1300, "≥ 1300 sujets TRAITÉS avec preuve existante (%d)" % r[C.TRAITE])
check(not r["dettes"], "ZÉRO dette : aucune preuve déclarée introuvable (%d)" % len(r["dettes"]))
check(len(r["backlog"]) > 0, "le backlog n'est pas vide (l'honnêteté du non-couvert)")

# ── FAUX=0 structurel : une preuve INEXISTANTE ne peut JAMAIS rendre un sujet « traité » ──
faux = S.Sujet("sujet piégé à preuve fantôme", "B-FAIT", "", "PARTIE I — piège", "", 0)
_sauve = C._REGLES_C
C._REGLES_C = ((__import__("re").compile(r"piégé"), "gate", "valide_fichier_qui_nexiste_pas.py", C.TRAITE),)
e, p = C.etat(faux)
C._REGLES_C = _sauve
check(e == C.NON_TRAITE and "INTROUVABLE" in p,
      "preuve fantôme -> NON TRAITÉ + dette DITE (jamais un « traité » déclaratif)")

# ── le non-borné est traité par le ROUTAGE, jamais par une réponse ──
nb = next(s for s in tous if s.code == "NB-SUBJ")
e, p = C.etat(nb)
check(e == C.TRAITE and "routage honnête" in p, "NB-SUBJ : traité = routé honnêtement (jamais répondu)")

# ── les roues déclarées comme preuves existent réellement dans le pont ──
import pont_grandeurs as P  # noqa: E402
noms_roues = {x["nom"] for x in P._ROUES}
for motif, genre, ref, _e in C._REGLES:
    if genre == "roue" and ref is not None:
        check(ref in noms_roues, "preuve-roue « %s » réellement câblée dans _ROUES" % ref)

# ── les annexes auto, si générées, sont cohérentes ──
if os.path.exists(S.DOC_AUTO):
    complet = S.charge_tout()
    check(len(complet) > len(tous) + 10000, "annexes auto : > 10 000 sujets supplémentaires (%d)" % len(complet))
    rc = C.rapport(complet)
    check(rc[C.NON_TRAITE] > rc[C.TRAITE],
          "l'honnêteté : le NON TRAITÉ domine (le backlog métiers est immense, et c'est DIT)")
    check(not rc["dettes"], "zéro dette sur la carte complète")
else:
    check(True, "(annexes auto non générées : outils/genere_sujets.py — sauté)")

print("=== valide_sujets : %d/%d ===" % (ok, ok + ko))
sys.exit(1 if ko else 0)
