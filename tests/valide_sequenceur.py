# -*- coding: utf-8 -*-
"""Gate SÉQUENCEUR (SPEC_TRONC_COMPREHENSION §11-§12, Phase 4) : la politique d'ordre des caps par acte.

Prouve les invariants qui rendent le séquenceur SÛR et UTILE :
  1. COLD-START : journal vide / acte hors prior / basse confiance -> ordre HISTORIQUE exact (zéro régression).
  2. PRIOR : un acte du prior remonte sa famille en tête.
  3. APPRENTISSAGE : un cap gagnant assez souvent pour un acte du prior REJOINT sa famille (bandit discret §11).
  4. SÛRETÉ FAUX=0 (l'invariant décisif) : réordonner PRÉSERVE l'ensemble des caps ET l'ordre relatif historique
     partout -> aucune paire de priorité vécue inversée -> la réponse ne peut pas changer.
  5. MESURE : la profondeur de sonde (nb de caps essayés avant le gagnant) DIMINUE avec la politique.
"""
import json
import os
import sys
import tempfile

_TMP = tempfile.mkdtemp()
os.environ["TRONC_ROUTAGE_PATH"] = os.path.join(_TMP, "routage.jsonl")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import sequenceur as S  # noqa: E402

_ok = [0]
_ko = [0]


def check(cond, label):
    if cond:
        _ok[0] += 1
    else:
        _ko[0] += 1
        print("  FAIL:", label)


# cascade FACTICE : l'ordre historique (comme la vraie boucle de repond) — (nom, handler-bidon).
CAPS = [(n, None) for n in ("avis_critere", "quotidien", "site", "avis", "challenge", "conversion",
                            "definition", "comptage", "comparaison_nway", "comparaison", "mesure_ambigue",
                            "synonyme_tete", "dimension", "traduction", "invention")]
NOMS = [n for n, _ in CAPS]


def _positions(ordre):
    return {n: i for i, (n, _) in enumerate(ordre)}


# ————————————————— (1) COLD-START : rien appris -> ordre historique EXACT —————————————————
S.recharge()
ordre, prio = S.ordonne("quotidien", CAPS, 0.9)
check([n for n, _ in ordre][:2] == ["quotidien", "site"], "prior quotidien -> famille en tête")
check(prio == {"quotidien", "site"}, "prioritaires présents renvoyés")
ordre, prio = S.ordonne("", CAPS, 0.9)
check([n for n, _ in ordre] == NOMS and prio == set(), "acte vide -> ordre historique intact, aucun prioritaire")
ordre, prio = S.ordonne("quotidien", CAPS, 0.5)
check([n for n, _ in ordre] == NOMS, "confiance < seuil -> ordre historique intact (on ne route pas au doute)")
ordre, prio = S.ordonne("interroger_fait", CAPS, 0.95)
check([n for n, _ in ordre] == NOMS and prio == set(),
      "acte factuel (hors prior) -> ordre historique (biais conservateur, jamais de famille inventée)")

# ————————————————— (4) SÛRETÉ FAUX=0 : ensemble préservé + ordre relatif historique jamais inversé —————————————————
for acte in ("quotidien", "demander_avis", "creer", "agir", "interroger_fait", ""):
    ordre, _ = S.ordonne(acte, CAPS, 0.95)
    check(sorted(n for n, _ in ordre) == sorted(NOMS), "SÛRETÉ : ensemble des caps préservé (%s)" % (acte or "∅"))
    pos = _positions(ordre)
    # toute paire (X avant Y dans l'historique) où X,Y sont du MÊME côté (tous deux remontés ou tous deux non)
    # reste (X avant Y). On vérifie les paires de priorité VÉCUES critiques :
    for x, y in [("avis_critere", "avis"), ("comparaison_nway", "comparaison"), ("mesure_ambigue", "synonyme_tete")]:
        check(pos[x] < pos[y], "SÛRETÉ : priorité vécue « %s avant %s » préservée (acte %s)" % (x, y, acte or "∅"))

# ————————————————— (3) APPRENTISSAGE : un cap gagnant assez souvent rejoint la famille de son acte —————————————————
S.SUPPORT_MIN = 3
with open(os.environ["TRONC_ROUTAGE_PATH"], "w", encoding="utf-8") as f:
    for _ in range(4):                                   # « challenge » tranche 4× pour demander_avis (≥ support)
        f.write(json.dumps({"date": "2026-07-08", "acte": "demander_avis", "cap": "challenge", "famille": False}) + "\n")
    for _ in range(2):                                   # « conversion » 2× seulement (< support) -> PAS appris
        f.write(json.dumps({"date": "2026-07-08", "acte": "demander_avis", "cap": "conversion", "famille": False}) + "\n")
    for _ in range(9):                                   # bruit sur un acte HORS prior -> jamais promu
        f.write(json.dumps({"date": "2026-07-08", "acte": "interroger_fait", "cap": "definition", "famille": False}) + "\n")
S.recharge()
prio = set(S.prioritaires("demander_avis"))
check("challenge" in prio, "APPRIS : « challenge » (4 succès) rejoint la famille demander_avis")
check("conversion" not in prio, "sous le support (2 < 3) -> PAS appris (anti-bruit)")
check(S.prioritaires("interroger_fait") == (),
      "acte hors prior -> jamais de famille apprise (même avec 9 succès) : sûreté avant tout")
ordre, prioset = S.ordonne("demander_avis", CAPS, 0.95)
tete = [n for n, _ in ordre][:3]
check(set(tete) == {"avis_critere", "avis", "challenge"} and tete == [n for n in NOMS if n in prioset],
      "APPRIS remonté en tête, MAIS toujours dans l'ordre HISTORIQUE (avis_critere < avis < challenge)")

# ————————————————— (5) MESURE : profondeur de sonde du gagnant, avant/après apprentissage —————————————————
def profondeur(acte, gagnant, conf=0.95):
    ordre, _ = S.ordonne(acte, CAPS, conf)
    return _positions(ordre)[gagnant]


S.recharge()
# « challenge » est en position 4 dans l'historique ; routé pour demander_avis (appris), il remonte.
p_hist = _positions(CAPS if False else [(n, None) for n in NOMS])["challenge"]
p_route = profondeur("demander_avis", "challenge")
check(p_route < p_hist, "MESURE : profondeur de sonde de « challenge » DIMINUE (%d -> %d) grâce au séquenceur" % (p_hist, p_route))

# rapport / couverture (diagnostic) — mesurés, jamais déclarés
rap = S.rapport()
check(rap.get("demander_avis", {}).get("challenge") == 4, "rapport : succès réels comptés par acte")
check("interroger_fait" not in rap or "definition" in rap.get("interroger_fait", {}),
      "rapport reflète le journal (les hors-prior sont comptés pour analyse, pas promus)")
tot, couv = S.couverture()
check(tot >= 15 and couv >= 0, "couverture : décisions totales journalisées comptées")

# ————————————————— (6) alias de compat : repond._FAMILLES_ACTES == sequenceur.PRIOR —————————————————
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "interface"))
os.environ.setdefault("LECTEUR_AMORCE_SEULE", "1")
import repond as R  # noqa: E402
check(R._FAMILLES_ACTES is S.PRIOR, "repond._FAMILLES_ACTES est bien l'alias de sequenceur.PRIOR (une source)")

print("valide_sequenceur :", _ok[0], "OK,", _ko[0], "KO")
sys.exit(1 if _ko[0] else 0)
