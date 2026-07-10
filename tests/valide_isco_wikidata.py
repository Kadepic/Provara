"""
VALIDE P8283 — le cliquet de l'élargissement d'alignement ISCO (le levier des chaînes métier).

CE QU'IL GARDE. Trois faux MESURÉS pendant la construction, chacun a sa contre-épreuve :

  • LE MILLÉSIME : P952 est l'ISCO-**88** (« acteur -> 2455 », « acrobate -> 3474ère ») ; P8283 est
    l'ISCO-08. Mêmes formes à 4 chiffres, sens différents — le module ne doit interroger QUE P8283.
  • L'HOMONYME : « compositeur » (musique) prenait le code 7321 du compositeur-TYPOGRAPHE, seul item
    à porter P8283. Un libellé multi-QID est écarté, TOUJOURS.
  • LE DÉSACCORD DE SOURCES : ESCO et P8283 divergent sur 25 métiers du chevauchement. La fusion
    (`_isco_du_store`) écarte le métier et le COMPTE — jamais d'arbitrage silencieux.

ANCRES NON CIRCULAIRES. Fixture écrite à la main ; « acteur de cinéma -> 2655 » est le code ISCO-08
publié par l'OIT, connu indépendamment.
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ingestion"))
import ingere_isco_wikidata as W

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


# ── 1) LE MILLÉSIME : seule P8283 est interrogée ─────────────────────────────────────────────────────
check("P8283" in W._REQUETE and "P952" not in W._REQUETE,
      "la requête interroge P8283 (ISCO-08), jamais P952 (ISCO-88 : faux de millésime silencieux)")
check("Q28640" in W._REQUETE and "Q101352" in W._REQUETE,
      "la garde de type de l'oracle est dans la requête (occupations, patronymes exclus)")

# ── 2) LE PARSE : groupe à 4 chiffres, bruit écarté ──────────────────────────────────────────────────
t = W.groupes_par_qid([{"qid": "Q33999", "code": "2655"}, {"qid": "Q33999", "code": "2655.1"},
                       {"qid": "Q484876", "code": "abc"}, {"qid": "", "code": "1234"}])
check(t == {"Q33999": {"2655"}}, "codes non numériques et QID vides écartés ; sous-codes tronqués au groupe")

# ── 3) L'ALIGNEMENT : les trois gardes ───────────────────────────────────────────────────────────────
PAR_QID = {"Q1": {"2655"},                 # acteur de cinéma (mono-QID)
           "Q2": {"7321"},                 # compositeur-typographe : seul homonyme à porter P8283
           "Q4": {"1111", "2222"}}         # item multi-groupes
LAB2QIDS = {"acteur ou actrice de cinéma": ["Q1"],
            "compositeur": ["Q2", "Q3"],   # homonyme : musique (Q3, sans P8283) + typographe (Q2)
            "chimiste": ["Q4"],
            "boulanger ou boulangère": ["Q5"]}
METIERS = list(LAB2QIDS) + ["déjà couvert"]
apparie, homonymes, multi = W.aligne(PAR_QID, LAB2QIDS, METIERS, deja={"déjà couvert"})
check(apparie == {"acteur ou actrice de cinéma": "2655"},
      "ancre OIT : acteur de cinéma -> 2655 (ISCO-08) ; et LUI SEUL passe")
check(homonymes == 1, "« compositeur » (multi-QID) écarté : le code viendrait du mauvais sens")
check(multi == 1, "item multi-groupes écarté")
check("déjà couvert" not in apparie, "un métier déjà aligné par ESCO n'entre pas (une source par métier)")
check("boulanger ou boulangère" not in apparie, "sans P8283 -> absent, jamais deviné")

# ── 4) LA FUSION : désaccord de sources -> métier écarté et compté ───────────────────────────────────
import ingere_bls_oes as B

_tmp = tempfile.mkdtemp(prefix="verax_isco_")
def _ecrit(nom, paires):
    with open(os.path.join(_tmp, nom + ".jsonl"), "w", encoding="utf-8") as f:
        f.write('{"_relation": "%s", "_categorie": "convention", "_source": "fixture"}\n' % nom)
        for e, v in paires:
            f.write(json.dumps({"entite": e, "valeur": v}, ensure_ascii=False) + "\n")

_ecrit("code_isco_metier", [("actuaire", "2120.1"), ("chimiste", "2113.0")])
_ecrit("code_isco_p8283_metier", [("chimiste", "3111"), ("géologue", "2114")])
_sauve = os.environ.get("LECTEUR_DATASETS_DIR")
os.environ["LECTEUR_DATASETS_DIR"] = _tmp
table = B._isco_du_store()
if _sauve is None:
    del os.environ["LECTEUR_DATASETS_DIR"]
else:
    os.environ["LECTEUR_DATASETS_DIR"] = _sauve
check(table.get("actuaire") == "2120", "fusion : le suffixe ESCO « .n » tombe, le groupe reste")
check(table.get("géologue") == "2114", "fusion : l'extension P8283 complète l'ESCO")
check("chimiste" not in table, "DÉSACCORD de sources (2113 vs 3111) -> métier ÉCARTÉ, jamais arbitré")

print("=== valide_isco_wikidata : %d ok, %d ko ===" % (ok, ko))
sys.exit(1 if ko else 0)
