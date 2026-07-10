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

    # ── FERMETURE ATOMIQUE, sur la carte RÉELLE (ne s'exerce que si les tables sont là) ────────────────
    metiers = [s for s in complet if s.partie.startswith("ANNEXE M")]
    axe_def = [s for s in metiers if "définition et périmètre" in s.libelle]
    check(bool(axe_def), "l'axe « définition et périmètre » existe dans la carte")

    tables = ("definition_esco_metier", "definition_metier", "surclasse_metier")
    if any(C._cles(t) is not None for t in tables):
        etats = {s: C.etat(s) for s in axe_def}
        traites = [s for s, (e, _) in etats.items() if e == C.TRAITE]
        non_tr = [s for s, (e, _) in etats.items() if e == C.NON_TRAITE]
        check(traites and non_tr, "axe « définition » : couverture PARTIELLE par entité (ni tout, ni rien)")
        check(all("vérifié par lookup" in etats[s][1] for s in traites),
              "chaque TRAITÉ nomme la table ET l'entité vérifiée")
        check(all(C._entite_annexe(s) in etats[s][1] for s in non_tr[:200]),
              "chaque NON TRAITÉ nomme l'entité manquante")
        cles = {t: C._cles(t) for t in tables}
        check(all(any(cles[t] is not None and C._entite_annexe(s) in cles[t] for t in tables) for s in traites),
              "toute entité TRAITÉE est présente sur le disque (aucune déclaration)")
        check(not any(any(cles[t] is not None and C._entite_annexe(s) in cles[t] for t in tables) for s in non_tr),
              "aucune entité NON TRAITÉE n'est en réalité présente (pas de faux négatif)")
        # anti-FAUX mesuré : ces valeurs de P106 ne sont PAS des métiers. Depuis l'oracle `est_metier`
        # (2026-07-12), elles ne sont plus DANS la carte du tout — un sujet faux se retire, il ne reste
        # pas « non traité ». (L'ancienne version exigeait leur PRÉSENCE : cliquet périmé par l'oracle.)
        faux = {"Abogado", "Anime", "Armée de l'air"}
        check(not any(C._entite_annexe(s) in faux for s in metiers),
              "« Abogado » / « Anime » / « Armée de l\'air » ne sont PLUS des sujets (oracle est_metier)")
    else:
        check(True, "(tables métiers absentes de ce store : cliquet réel non applicable — voir la FIXTURE)")

    # 4) plus AUCUN axe métier « sans source » : les huit sont soit routés, soit MIX par entité.
    #    (Le cliquet vit désormais en §5 : PARTIEL par entité, JAMAIS TRAITÉ.)

    # 5) les axes MIX peuvent être PARTIELS par entité, JAMAIS TRAITÉS : « gestes » (le tour de main
    # tacite reste non borné), « formation » (le RNCP ferme la part FRANÇAISE ; la formation varie
    # par pays et par année), « normes » (REGPROF/ESCO ferment la réglementation d'ACCÈS ; les
    # normes techniques restent non couvertes) et « rémunération » (BLS OEWS ferme la part
    # ÉTATS-UNIS ; les autres pays restent non couverts).
    for axe, pourquoi in (("gestes et savoir-faire", "la part tacite reste non bornée"),
                          ("formation, diplômes", "les autres systèmes nationaux restent non couverts"),
                          ("normes, réglementation", "les normes techniques restent non couvertes"),
                          ("rémunération médiane", "les autres pays restent non couverts"),
                          ("outils, machines", "l'outillage réel n'est borné par aucun référentiel"),
                          ("risques professionnels", "la prévention et la part française restent non couvertes")):
        lot = [s for s in metiers if axe in s.libelle]
        check(lot and not any(C.etat(s)[0] == C.TRAITE for s in lot),
              "axe MIX « %s » : aucun sujet déclaré TRAITÉ (%s)" % (axe[:20], pourquoi))
else:
    check(True, "(annexes auto non générées : outils/genere_sujets.py — sauté)")


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
# CLIQUET D'ATOMICITÉ SUR FIXTURE — il s'exerce TOUJOURS, même sans la base réelle.
#
# Pourquoi : la première version de ce cliquet ne se déclenchait que si les tables métiers étaient présentes
# dans le store. Or la suite épingle l'ÉCHANTILLON embarqué (où elles ne sont pas). Le cliquet le plus
# important du mandat — « jamais un axe couvert en bloc » — ne protégeait donc RIEN en intégration.
# On le rejoue ici sur un store FABRIQUÉ : deux métiers, un seul présent dans la table.
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
import json
import tempfile

_ANNEXE_M = "ANNEXE M — MÉTIERS RÉELS × AXES ATOMIQUES"


def _sujet(libelle):
    return S.Sujet(libelle=libelle, code="B-CONV", raison="fixture", partie=_ANNEXE_M, section="M.1", ligne=1)


_garde_dossier, _garde_cache = C._DOSSIER_STORE, dict(C._CACHE_CLES)
with tempfile.TemporaryDirectory() as _tmp:
    for _table, _entites in (("definition_metier", ["boulanger ou boulangère"]),
                             ("geste_metier", ["boulanger ou boulangère"]),
                             ("certification_rncp_metier", ["boulanger ou boulangère"]),
                             ("profession_reglementee_metier", ["boulanger ou boulangère"]),
                             ("salaire_median_soc_us_metier", ["boulanger ou boulangère"]),
                             ("outil_technologie_soc_metier", ["boulanger ou boulangère"]),
                             ("risque_professionnel_soc_metier", ["boulanger ou boulangère"])):
        with open(os.path.join(_tmp, _table + ".jsonl"), "w", encoding="utf-8") as _f:
            _f.write('{"_relation": "%s", "_categorie": "convention", "_source": "fixture"}\n' % _table)
            for _e in _entites:
                _f.write(json.dumps({"entite": _e, "valeur": "x"}, ensure_ascii=False) + "\n")
    C._DOSSIER_STORE = _tmp
    C._CACHE_CLES.clear()

    _present = _sujet("boulanger ou boulangère — définition et périmètre du métier")
    _absent = _sujet("métier fantôme — définition et périmètre du métier")
    _e_pres, _p_pres = C.etat(_present)
    _e_abs, _p_abs = C.etat(_absent)
    check(_e_pres == C.TRAITE, "FIXTURE : le métier PRÉSENT dans la table est TRAITÉ")
    check("boulanger ou boulangère" in _p_pres and "definition_metier" in _p_pres,
          "FIXTURE : la preuve nomme la table ET l'entité")
    check(_e_abs == C.NON_TRAITE, "FIXTURE : le métier ABSENT n'est jamais TRAITÉ (pas de couverture en bloc)")
    check("métier fantôme" in _p_abs, "FIXTURE : le refus nomme l'entité manquante")

    # l'axe « gestes » est MIX : présent -> PARTIEL, jamais TRAITÉ.
    _g_pres = C.etat(_sujet("boulanger ou boulangère — gestes et savoir-faire techniques"))
    _g_abs = C.etat(_sujet("métier fantôme — gestes et savoir-faire techniques"))
    check(_g_pres[0] == C.PARTIEL, "FIXTURE : gestes d'un métier couvert -> PARTIEL (part codifiée seule)")
    check("part codifiée seule" in _g_pres[1], "FIXTURE : le PARTIEL dit que seule la part codifiée est couverte")
    check(_g_abs[0] == C.NON_TRAITE, "FIXTURE : gestes d'un métier absent -> NON TRAITÉ")

    # l'axe « formation » est MIX lui aussi : présent -> PARTIEL (part française RNCP), jamais TRAITÉ.
    _f_pres = C.etat(_sujet("boulanger ou boulangère — formation, diplômes et voies d'accès"))
    _f_abs = C.etat(_sujet("métier fantôme — formation, diplômes et voies d'accès"))
    check(_f_pres[0] == C.PARTIEL, "FIXTURE : formation d'un métier couvert -> PARTIEL (part française seule)")
    check("FRANÇAISE" in _f_pres[1], "FIXTURE : le PARTIEL dit que seule la part française est couverte")
    check(_f_abs[0] == C.NON_TRAITE, "FIXTURE : formation d'un métier absent -> NON TRAITÉ")

    # l'axe « normes » est MIX : réglementation d'ACCÈS (REGPROF/ESCO) -> PARTIEL, jamais TRAITÉ.
    _n_pres = C.etat(_sujet("boulanger ou boulangère — normes, réglementation et certifications"))
    _n_abs = C.etat(_sujet("métier fantôme — normes, réglementation et certifications"))
    check(_n_pres[0] == C.PARTIEL, "FIXTURE : normes d'un métier couvert -> PARTIEL (accès seul)")
    check("ACCÈS" in _n_pres[1], "FIXTURE : le PARTIEL dit que seule la réglementation d'accès est couverte")
    check(_n_abs[0] == C.NON_TRAITE,
          "FIXTURE : normes d'un métier absent -> NON TRAITÉ (l'absence de REGPROF n'est pas un fait)")

    # l'axe « rémunération » est MIX : part États-Unis (BLS OEWS) -> PARTIEL, jamais TRAITÉ.
    _r_pres = C.etat(_sujet("boulanger ou boulangère — rémunération médiane (pays et année donnés)"))
    _r_abs = C.etat(_sujet("métier fantôme — rémunération médiane (pays et année donnés)"))
    check(_r_pres[0] == C.PARTIEL, "FIXTURE : rémunération d'un métier couvert -> PARTIEL (États-Unis seuls)")
    check("ÉTATS-UNIS" in _r_pres[1], "FIXTURE : le PARTIEL dit que seule la part États-Unis est couverte")
    check(_r_abs[0] == C.NON_TRAITE, "FIXTURE : rémunération d'un métier absent -> NON TRAITÉ")

    # l'axe « outils » est MIX : part codifiée O*NET -> PARTIEL, jamais TRAITÉ.
    _o_pres = C.etat(_sujet("boulanger ou boulangère — outils, machines et logiciels du métier"))
    _o_abs = C.etat(_sujet("métier fantôme — outils, machines et logiciels du métier"))
    check(_o_pres[0] == C.PARTIEL, "FIXTURE : outils d'un métier couvert -> PARTIEL (part codifiée O*NET)")
    check("O*NET" in _o_pres[1], "FIXTURE : le PARTIEL nomme O*NET et sa granularité")
    check(_o_abs[0] == C.NON_TRAITE, "FIXTURE : outils d'un métier absent -> NON TRAITÉ")

    # l'axe « risques » est MIX : part mesurée BLS SOII -> PARTIEL, jamais TRAITÉ.
    _q_pres = C.etat(_sujet("boulanger ou boulangère — risques professionnels et prévention"))
    _q_abs = C.etat(_sujet("métier fantôme — risques professionnels et prévention"))
    check(_q_pres[0] == C.PARTIEL, "FIXTURE : risques d'un métier couvert -> PARTIEL (part mesurée US)")
    check("SOII" in _q_pres[1], "FIXTURE : le PARTIEL nomme le SOII et sa part")
    check(_q_abs[0] == C.NON_TRAITE, "FIXTURE : risques d'un métier absent -> NON TRAITÉ")

    # le NON BORNÉ reste traité par le routage honnête (ce n'est pas une réponse inventée).
    _e, _ = C.etat(_sujet("boulanger ou boulangère — « ce métier est-il fait pour moi ? »"))
    check(_e == C.TRAITE, "FIXTURE : le NB-SUBJ est traité par routage honnête")

    # SABOTAGE : si un axe redevenait « couvert en bloc », le cliquet DOIT rougir.
    _sauve = C._AXES_M
    C._AXES_M = tuple((rx, "routage" if "outils" in rx.pattern else m, t, r) for rx, m, t, r in C._AXES_M)
    _sabote, _ = C.etat(_sujet("métier fantôme — outils, machines et logiciels"))
    C._AXES_M = _sauve
    check(_sabote == C.TRAITE, "FIXTURE (contre-épreuve) : un axe déclaré en bloc EST détectable")
    _reel, _ = C.etat(_sujet("métier fantôme — outils, machines et logiciels"))
    check(_reel == C.NON_TRAITE, "FIXTURE : après restauration, l'axe « outils » redevient NON TRAITÉ")

C._DOSSIER_STORE = _garde_dossier
C._CACHE_CLES.clear()
C._CACHE_CLES.update(_garde_cache)

print("=== valide_sujets : %d/%d ===" % (ok, ok + ko))
sys.exit(1 if ko else 0)
