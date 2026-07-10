"""
VALIDE l'ORACLE DE MÉTIER — le cliquet qui empêche la carte de compter des non-métiers.

CE QU'IL GARDE. `outils/genere_sujets.py` peuplait l'ANNEXE M avec CHAQUE valeur distincte de la table
`occupation_personne`. Trois familles de valeurs n'y sont pas des métiers :

  • les NOMS DE FAMILLE et objets que Wikidata range sous P106 (« Abogado », « Anime », « Armée de l'air ») ;
  • les ÉNUMÉRATIONS fabriquées par `ingestion/ingere_celebres.py`, qui joint les occupations des
    personnalités célèbres (« physicien, professeur d'université et philosophe ») ;
  • les ENTREPRISES que la hiérarchie Wikidata place sous « profession » (« Mann », constructeur de camions).

Aucune ne peut JAMAIS être traitée : un nom de famille n'a ni définition, ni gestes, ni risques
professionnels. Les compter fabriquait 38 703 sujets inépuisables — un backlog qui ment.

ANCRES NON CIRCULAIRES. La fixture est écrite ici, à la main. Le filtre est un LOOKUP dans `est_metier` :
le test ne recalcule jamais l'oracle, il l'ÉCRIT et vérifie que le filtre l'interroge.

CONTRE-ÉPREUVE DE SABOTAGE. On vide l'oracle : le générateur doit alors rendre ZÉRO métier. S'il en rendait
encore, c'est qu'il ne consulte pas l'oracle et le cliquet ne garderait rien.

CONTRE-ÉPREUVE D'ABSENCE. Sans la table `est_metier`, le générateur doit LEVER, jamais retomber sur la liste
brute : régénérer une carte gonflée en silence est pire que ne rien régénérer.
"""
import json
import os
import sys
import tempfile

import genere_sujets as G

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def _ecrit(dossier, table, paires):
    with open(os.path.join(dossier, table + ".jsonl"), "w", encoding="utf-8") as f:
        f.write('{"_relation": "%s", "_categorie": "convention", "_source": "fixture"}\n' % table)
        for e, v in paires:
            f.write(json.dumps({"entite": e, "valeur": v}, ensure_ascii=False) + "\n")


# ── LA FIXTURE : un store fabriqué, indépendant de la base réelle ─────────────────────────────────────
VRAIS = ("boulanger ou boulangère", "avocat ou avocate", "médecin")
FAUX = (
    "Abogado",                                                    # nom de famille (Wikidata P106)
    "Anime",                                                      # objet
    "Mann",                                                       # entreprise (constructeur de camions)
    "physicien, professeur d'université et philosophe",           # énumération fabriquée (ingere_celebres)
    "acteur ou actrice, basketteur ou basketteuse et athlète professionnel",
)

_TMP = tempfile.mkdtemp(prefix="verax_oracle_")
_ecrit(_TMP, "occupation_personne", [("p%d" % i, v) for i, v in enumerate(VRAIS + FAUX)])
_ecrit(_TMP, "est_metier", [(v, "Q%d" % (100 + i)) for i, v in enumerate(VRAIS)])
_ORIG = G._STORE
G._STORE = _TMP

# ── 1) LE FILTRE : les vrais passent, les faux tombent ────────────────────────────────────────────────
metiers, n_oracle, ecartes = G.metiers_de_la_carte()
check(n_oracle == 3, "l'oracle de la fixture porte 3 libellés")
check(sorted(metiers) == sorted(VRAIS), "seuls les métiers ATTESTÉS sont retenus")
check(ecartes == len(FAUX), "les %d non-métiers sont écartés et COMPTÉS (mesuré : %d)" % (len(FAUX), ecartes))
for f in FAUX:
    check(f not in metiers, "« %s » n'est pas un métier" % f[:46])
for v in VRAIS:
    check(v in metiers, "« %s » est un métier" % v)

# ── 2) AUCUNE HEURISTIQUE DE CHAÎNE : la virgule ne décide de rien ────────────────────────────────────
# « Employés de réception, guichetiers et assimilés » est UN libellé CITP unique. S'il est attesté, il passe,
# bien qu'il contienne « , » et « et ». Un filtre qui découperait sur la virgule le perdrait.
CITP = "Employés de réception, guichetiers et assimilés"
_ecrit(_TMP, "occupation_personne", [("p%d" % i, v) for i, v in enumerate(VRAIS + FAUX + (CITP,))])
_ecrit(_TMP, "est_metier", [(v, "Q%d" % (100 + i)) for i, v in enumerate(VRAIS + (CITP,))])
metiers2, _, _ = G.metiers_de_la_carte()
check(CITP in metiers2, "un libellé CITP composé, s'il est ATTESTÉ, reste un métier")
check("physicien, professeur d'université et philosophe" not in metiers2,
      "une énumération fabriquée, elle, reste écartée — la source tranche, pas la ponctuation")

# ── 3) CONTRE-ÉPREUVE DE SABOTAGE : oracle vide -> zéro métier ────────────────────────────────────────
_ecrit(_TMP, "est_metier", [])
metiers3, n3, ec3 = G.metiers_de_la_carte()
check(n3 == 0, "oracle vidé")
check(metiers3 == [], "SABOTAGE : oracle vide -> AUCUN métier (le filtre consulte bien l'oracle)")
check(ec3 == len(VRAIS + FAUX + (CITP,)), "toutes les valeurs sont alors écartées, et comptées")

# ── 4) CONTRE-ÉPREUVE D'ABSENCE : pas d'oracle -> on LÈVE, on ne retombe pas sur la liste brute ────────
os.remove(os.path.join(_TMP, "est_metier.jsonl"))
try:
    G.metiers_de_la_carte()
    check(False, "table absente -> doit lever SystemExit")
except SystemExit as e:
    check("est_metier" in str(e), "table absente -> SystemExit qui NOMME la table manquante")
    check("ingere_metiers_attestes" in str(e), "… et qui dit comment la produire")

# ── 5) L'ORACLE RÉEL, s'il est présent (sinon on ne prétend rien) ──────────────────────────────────────
G._STORE = _ORIG
if os.path.exists(os.path.join(_ORIG, "est_metier.jsonl")):
    reels = G._entites("est_metier")
    check(len(reels) > 1000, "oracle réel : plus de 1000 libellés attestés (%d)" % len(reels))
    check("boulanger ou boulangère" in reels, "oracle réel : « boulanger ou boulangère » attesté")
    check("Abogado" not in reels, "oracle réel : « Abogado » (nom de famille) NON attesté")
    check("Anime" not in reels, "oracle réel : « Anime » NON attesté")
    check("Mann" not in reels, "oracle réel : « Mann » (entreprise) NON attesté")

    # DEUX GARDES QUI SE COUVRENT L'UNE L'AUTRE, et la seconde n'est PAS redondante.
    #   • L'ORACLE (type P31/P279* Q28640) tue les valeurs de P106 qui ne sont pas des occupations :
    #     « Abogado » (nom de famille), « Anime », « Mann » (entreprise).
    #   • L'USAGE P106 (appartenir aux valeurs de `occupation_personne`) tue les items TYPÉS occupation que
    #     personne n'exerce. Mesuré : Q136296945 « Plaque de reliure crucifixion, saintes femmes au tombeau,
    #     ascension et Christ bénissant » est un IVOIRE (P31 -> Q351853), et la chaîne P279* de Wikidata le
    #     raccroche à « profession ». Zéro personne ne l'a pour occupation : il n'entre pas dans la carte.
    # L'oracle contient donc, légitimement, des libellés à virgules — des groupes CITP (« Manœuvres des
    # mines, du bâtiment et des travaux publics… »). Un filtre qui découperait sur la virgule les perdrait.
    citp = [m for m in reels if m.count(",") >= 2 and " et " in m]
    check(len(citp) >= 2, "oracle réel : des libellés CITP à virgules existent (%d) — pas d'heuristique de "
                          "ponctuation possible" % len(citp))
    metiers_reels, _, ecartes_reels = G.metiers_de_la_carte()
    check("Plaque de reliure crucifixion, saintes femmes au tombeau, ascension et Christ bénissant"
          not in metiers_reels, "l'ivoire typé « profession » n'atteint PAS la carte (garde d'usage P106)")
    check("boulanger ou boulangère" in metiers_reels, "carte réelle : « boulanger ou boulangère » est un métier")
    for f in ("Abogado", "Anime", "Mann"):
        check(f not in metiers_reels, "carte réelle : « %s » n'est pas un métier" % f)
    # ANCRES NOMMÉES, mesurées sur le disque le 2026-07-12. Aucune règle de ponctuation ici : les
    # énumérations fabriquées sont citées une à une, et les VRAIS métiers à virgules doivent survivre.
    # (Écrire `"," in m and " et " in m -> fabriqué` aurait supprimé « voyageur, représentant et placier »,
    #  qui est un métier, et « professeurs des écoles, instituteurs et assimilés », qui est une catégorie PCS.)
    for e in ("acteur ou actrice de cinéma, acteur ou actrice de théâtre et acteur ou actrice de genre",
              "acteur ou actrice de cinéma, acteur ou actrice de théâtre et acteur ou actrice de voix-off",
              "acteur ou actrice de cinéma, acteur ou actrice de télévision et chanteur ou chanteuse"):
        check(e not in metiers_reels, "énumération fabriquée écartée : « %s… »" % e[:38])
    for vrai in ("voyageur, représentant et placier", "professeurs des écoles, instituteurs et assimilés",
                 "professions de l'information, des arts et des spectacles"):
        check(vrai in metiers_reels, "vrai métier à virgules CONSERVÉ : « %s »" % vrai)
    check(ecartes_reels > 1000, "carte réelle : les non-métiers écartés sont comptés (%d)" % ecartes_reels)
else:
    print("  (oracle réel absent de ce store : les contrôles 5 sont SAUTÉS, rien n'est prétendu)")

print(f"\n=== valide_oracle_metier : {ok}/{ok+ko} ===")
sys.exit(0 if ko == 0 else 1)
