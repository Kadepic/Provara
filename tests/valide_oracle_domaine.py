"""
VALIDE l'ORACLE DE DOMAINE — le cliquet qui empêche l'ANNEXE D de compter des non-domaines.

CE QU'IL GARDE. `genere_sujets` prenait CHAQUE valeur distincte de `domaine_travail` (P101) pour un
domaine. Or P101 pointe aussi des PERSONNES (« Friedrich Nietzsche » — le philologue qui l'étudie), des
ORGANISATIONS (UNICEF — mésusage employeur), des ENTITÉS GÉOGRAPHIQUES (« France »). « Résultats établis
du domaine Friedrich Nietzsche » est un sujet MAL FORMÉ : 906 sujets-domaines faux, un backlog qui ment.

DEUX PIÈGES PROPRES AUX DOMAINES (absents du cas métier) :
  • la SUR-EXCLUSION : juger les PORTEURS du libellé tuait « peinture » (une page d'homonymie porte
    aussi ce libellé) — la garde juge les QID RÉELLEMENT UTILISÉS comme cible de P101, et un libellé
    n'est retiré que si TOUTES ses cibles sont exclues ;
  • la COLLISION DE CLÉS : « physique »/« Physique » émis séparément se rejetaient en multivalué dans
    `fonctionnel` et le domaine sortait de l'oracle EN SILENCE (139 rejets mesurés, dont « physique »).
    L'oracle groupe par la clé `_sans_articles` et émet UNE surface.

CONTRE-ÉPREUVE DE SABOTAGE : oracle vidé -> zéro domaine ; table retirée -> le générateur LÈVE.
"""
import json
import os
import sys
import tempfile

import genere_sujets as G
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ingestion"))
import ingere_domaines_attestes as O

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


# ── 1) L'ORACLE : gardes par QID utilisés ─────────────────────────────────────────────────────────────
CIBLES = [
    ("Q413", "physique"), ("Q413", "Physique"),          # collision de clés : DEUX surfaces, même domaine
    ("Q11629", "peinture"), ("Q1272381", "peinture"),    # homonymie : art (gardé) + page d'homonymie (exclue)
    ("Q9358", "Friedrich Nietzsche"),                    # personne : TOUTES ses cibles exclues
    ("Q142", "France"),                                  # entité géographique
    ("Q1420", "gospel"),                                 # genre : traitable, GARDÉ
]
EXCLUS = {"Q1272381", "Q9358", "Q142"}
paires = O.oracle(CIBLES, EXCLUS)
noms = {p[0] for p in paires}
cles = { }
check(len([n for n in noms if n.lower() == "physique"]) == 1,
      "collision « physique »/« Physique » -> UNE surface (le multivalué silencieux est mort)")
check("peinture" in noms, "« peinture » gardé : sa cible ART vit, la page d'homonymie ne le tue pas")
check("Friedrich Nietzsche" not in noms, "une PERSONNE n'est pas un domaine")
check("France" not in noms, "une ENTITÉ GÉOGRAPHIQUE n'est pas un domaine")
check("gospel" in noms, "un genre traitable RESTE : retirer un sujet traitable serait l'autre mesure fausse")
d = dict(paires)
check(d.get("peinture") == "Q11629", "l'attestation ne publie que les cibles NON exclues")

# ── 2) LE FILTRE du générateur, sur fixture ───────────────────────────────────────────────────────────
def _ecrit(dossier, table, ps):
    with open(os.path.join(dossier, table + ".jsonl"), "w", encoding="utf-8") as f:
        f.write('{"_relation": "%s", "_categorie": "convention", "_source": "fixture"}\n' % table)
        for e, v in ps:
            f.write(json.dumps({"entite": e, "valeur": v}, ensure_ascii=False) + "\n")

_TMP = tempfile.mkdtemp(prefix="verax_dom_")
_ecrit(_TMP, "domaine_travail", [("p%d" % i, v) for i, v in enumerate(
    ["physique", "la physique", "Friedrich Nietzsche", "France", "gospel"])])
_ecrit(_TMP, "est_domaine", [("Physique", "Q413"), ("gospel", "Q1420")])
_ORIG = G._STORE
G._STORE = _TMP
try:
    domaines, n_oracle, ecartes = G.domaines_de_la_carte()
    check(sorted(domaines) == ["gospel", "la physique", "physique"],
          "le lookup passe par la CLÉ (« physique », « la physique » ≡ « Physique ») ; les faux tombent")
    check(ecartes == 2, "les non-domaines sont écartés et COMPTÉS (mesuré : %d)" % ecartes)

    # SABOTAGE : oracle vidé -> zéro domaine (le filtre consulte VRAIMENT l'oracle)
    _ecrit(_TMP, "est_domaine", [])
    G._entites.cache_clear() if hasattr(G._entites, "cache_clear") else None
    domaines2, _, _ = G.domaines_de_la_carte()
    check(domaines2 == [], "SABOTAGE : oracle vidé -> zéro domaine")

    # ABSENCE : table retirée -> le générateur LÈVE, jamais la liste brute
    os.remove(os.path.join(_TMP, "est_domaine.jsonl"))
    try:
        G.domaines_de_la_carte()
        check(False, "sans oracle le générateur doit LEVER")
    except SystemExit as e:
        check("est_domaine" in str(e), "l'erreur NOMME la table manquante")
finally:
    G._STORE = _ORIG

print("=== valide_oracle_domaine : %d ok, %d ko ===" % (ok, ko))
sys.exit(1 if ko else 0)
